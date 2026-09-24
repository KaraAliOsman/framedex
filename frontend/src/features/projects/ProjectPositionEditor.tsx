import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  engineSystems,
  positionsCreate,
  positionsRetrieve,
  positionsUpdate,
  projectDesignOptions,
} from "../../api/generated/dekopen";

import type {
  EngineAssemblyCalculateResponse,
  EngineCalculateResponse,
  PositionDesignRequest,
  PositionResponse,
} from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { ApiError } from "../../api/apiMutator";
import { UnsavedChangesGuard } from "../../app/UnsavedChangesGuard";
import { t } from "../../i18n/es-CL";
import { type CanvasDesignInputs, useCanvasStore } from "../canvas/canvasStore";
import { AssemblyEditor } from "../canvas/AssemblyEditor";
import type { IntentNode, Opening } from "../canvas/intentEditing";
import { starterContextSize, type StarterDefinition } from "../canvas/designLibrary";
import { resolveMembers } from "../canvas/members";
import { StarterGallery } from "../canvas/StarterGallery";
import {
  elevationEnvelopeMm,
  isProductModel,
  isSingleUnit,
  removeUnit,
  wrapTreeAsProduct,
  type ProductJson,
} from "../canvas/productEditing";

import "./projects.css";

export function ProjectPositionEditor(): JSX.Element {
  const { id = "", posId = "" } = useParams();
  const [query] = useSearchParams();
  const copyId = posId ? "" : (query.get("copy") ?? "");
  const org = useAuthSession().me?.active_organization;
  if (!org || !["OWNER", "ESTIMATOR"].includes(org.role))
    return <p role="alert">{t("projects.denied")}</p>;
  return (
    <PositionWorkspace
      key={`${org.id}:${id}:${posId}:${copyId}`}
      orgId={org.id}
      projectId={id}
      positionId={posId}
      copyId={copyId}
    />
  );
}

function starterTree(opening: Opening): IntentNode {
  return { id: crypto.randomUUID(), type: "BAY", opening_type: opening };
}

function initial(): CanvasDesignInputs {
  const product = wrapTreeAsProduct(starterTree("FIXED"), "1000.00", "1000.00");
  return {
    systemId: null,
    nominalWidthMm: "1000.00",
    nominalHeightMm: "1000.00",
    color: "WHITE",
    parametricTree: product.assembly.modules[0]?.tree ?? starterTree("FIXED"),
    product,
  };
}

/** Fill catalog-driven values that are uniquely determined: a coupling without
 * a coupler gets the catalog's only coupler; splits without a mullion get the
 * catalog's only mullion of that direction; bays without glazing get the
 * catalog's only thickness (the spec defaults to the same monolithic value).
 * Ambiguity stays unresolved — the choice is surfaced in the inspector,
 * never guessed. */
function resolveDefaults(
  product: ProductJson,
  couplerSkus: string[],
  mullionSkus: { SPLIT_V?: string; SPLIT_H?: string },
  glassThicknessMm?: string,
  panelSku?: string,
): ProductJson {
  let next = product;
  if (couplerSkus.length === 1) {
    const sku = couplerSkus[0]!;
    for (const coupling of next.assembly.couplings) {
      if (coupling.coupler_profile_sku === null) {
        next = {
          ...next,
          assembly: {
            ...next.assembly,
            couplings: next.assembly.couplings.map((item) =>
              item.id === coupling.id ? { ...item, coupler_profile_sku: sku } : item,
            ),
          },
        };
      }
    }
  }
  const needsFill = (node: IntentNode): boolean => {
    const missingMullion =
      (node.type === "SPLIT_V" || node.type === "SPLIT_H") &&
      !node.mullion_profile_sku &&
      mullionSkus[node.type] !== undefined;
    const missingGlass =
      node.type === "BAY" &&
      glassThicknessMm !== undefined &&
      (!node.glass_thickness_mm || !node.glass_spec);
    const missingPanel =
      node.type === "BAY" &&
      node.opening_type === "DOOR_ENTRY" &&
      !node.panel_article_sku &&
      panelSku !== undefined;
    return (
      missingMullion || missingGlass || missingPanel || (node.children?.some(needsFill) ?? false)
    );
  };
  const fill = (node: IntentNode): IntentNode => {
    let updated = node;
    if (
      (node.type === "SPLIT_V" || node.type === "SPLIT_H") &&
      !node.mullion_profile_sku &&
      mullionSkus[node.type] !== undefined
    ) {
      updated = { ...updated, mullion_profile_sku: mullionSkus[node.type] };
    }
    if (updated.type === "BAY" && glassThicknessMm !== undefined) {
      if (!updated.glass_thickness_mm)
        updated = { ...updated, glass_thickness_mm: glassThicknessMm };
      if (!updated.glass_spec) updated = { ...updated, glass_spec: glassThicknessMm };
    }
    if (updated.type === "BAY" && updated.opening_type === "DOOR_ENTRY" && panelSku !== undefined) {
      if (!updated.panel_article_sku) updated = { ...updated, panel_article_sku: panelSku };
    }
    return { ...updated, children: node.children?.map(fill) };
  };
  if (next.assembly.modules.some((module) => needsFill(module.tree))) {
    next = {
      ...next,
      assembly: {
        ...next.assembly,
        modules: next.assembly.modules.map((module) => ({
          ...module,
          tree: fill(module.tree),
        })),
      },
    };
  }
  return next;
}

/** The design object that save() would send — used both by save and by the
 * dirty baseline, so they can never disagree about what "unchanged" means. */
function designPayload(inputs: CanvasDesignInputs): PositionDesignRequest | null {
  const product = inputs.product;
  if (product === null || !inputs.systemId || inputs.color !== "WHITE") return null;
  const single = isSingleUnit(product) ? product.assembly.modules[0] : undefined;
  return single !== undefined
    ? {
        system_id: inputs.systemId,
        nominal_width_mm: single.width_mm,
        nominal_height_mm: single.height_mm,
        color: inputs.color,
        parametric_tree: single.tree,
      }
    : {
        system_id: inputs.systemId,
        nominal_width_mm: elevationEnvelopeMm(product).width.toFixed(2),
        nominal_height_mm: elevationEnvelopeMm(product).height.toFixed(2),
        color: inputs.color,
        parametric_tree: product,
      };
}

/** JSON.stringify with recursively sorted keys — a stable identity for
 * comparing loaded/saved designs against the live inputs. */
function canonicalize(value: unknown): string {
  const order = (node: unknown): unknown => {
    if (Array.isArray(node)) return node.map(order);
    if (node !== null && typeof node === "object") {
      return Object.fromEntries(
        Object.keys(node as Record<string, unknown>)
          .sort()
          .map((key) => [key, order((node as Record<string, unknown>)[key])]),
      );
    }
    return node;
  };
  return JSON.stringify(order(value));
}

function PositionWorkspace({
  orgId,
  projectId,
  positionId,
  copyId,
}: {
  orgId: string;
  projectId: string;
  positionId: string;
  copyId: string;
}): JSX.Element {
  const navigate = useNavigate();
  const [loaded, setLoaded] = useState(false);
  const [saved, setSaved] = useState<PositionResponse | null>(null);
  const [result, setResult] = useState<EngineCalculateResponse | null>(null);
  const [location, setLocation] = useState("");
  const [quantity, setQuantity] = useState("1");
  // null baseline = nothing persisted yet for this route (copy) → always dirty.
  const [baseline, setBaseline] = useState<{
    design: string;
    location: string;
    quantity: string;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const mutationLock = useRef(false);
  const [message, setMessage] = useState("");
  const [uncertainCreate, setUncertainCreate] = useState(false);
  const [assemblyEval, setAssemblyEval] = useState<EngineAssemblyCalculateResponse | null>(null);
  const [createdId, setCreatedId] = useState<string | null>(null);
  // New positions open on the design library (the start point); saved ones go
  // straight to the canvas — picking a starter collapses it.
  const [libraryOpen, setLibraryOpen] = useState(!positionId && !copyId);
  const generation = useRef(0);
  const inputs = useCanvasStore((s) => s.inputs);
  const canUndo = useCanvasStore((s) => s.past.length > 0);
  const canRedo = useCanvasStore((s) => s.future.length > 0);
  const systemId = inputs.systemId ?? "";
  const requestOptions = { headers: { "X-Organization-ID": orgId } };

  const systems = useQuery({
    queryKey: ["project-systems", orgId],
    queryFn: async () => {
      const response = await engineSystems(requestOptions);
      if (response.status !== 200) throw new Error("load");
      return response.data.systems;
    },
    retry: false,
  });
  const options = useQuery({
    queryKey: ["project-design-options", orgId, systemId],
    queryFn: async () => {
      const response = await projectDesignOptions(systemId, requestOptions);
      if (response.status !== 200) throw new Error("load");
      return response.data;
    },
    enabled: !!systemId,
    retry: false,
  });

  useEffect(() => {
    let active = true;
    if (!positionId && !copyId) {
      const blank = initial();
      useCanvasStore.getState().loadDesign(blank);
      setBaseline({ design: canonicalize(designPayload(blank)), location: "", quantity: "1" });
      setLoaded(true);
    } else
      void positionsRetrieve(positionId || copyId, { headers: { "X-Organization-ID": orgId } })
        .then((response) => {
          if (!active) return;
          if (response.status !== 200 || response.data.project_id !== projectId)
            throw new Error("unavailable");
          const item = response.data;

          if (item.design.color !== "WHITE") throw new Error("unsupported color");
          const tree = item.design.parametric_tree;
          const product: ProductJson = isProductModel(tree)
            ? tree
            : wrapTreeAsProduct(
                tree as IntentNode,
                item.design.nominal_width_mm,
                item.design.nominal_height_mm,
              );
          useCanvasStore.getState().loadDesign({
            systemId: item.design.system_id,
            nominalWidthMm: item.design.nominal_width_mm,
            nominalHeightMm: item.design.nominal_height_mm,
            color: "WHITE",
            parametricTree:
              product.assembly.modules.at(0)?.tree ??
              ({ id: "m1", type: "BAY", opening_type: "FIXED" } as IntentNode),
            product,
          });
          setSaved(copyId ? null : item);
          setBaseline(
            copyId
              ? null
              : {
                  design: canonicalize(item.design),
                  location: item.location_tag ?? "",
                  quantity: String(item.quantity),
                },
          );
          setLocation(item.location_tag ?? "");
          setQuantity(String(item.quantity));
          setResult(item.bom);
          setLoaded(true);
        })
        .catch(() => {
          if (active) setMessage(t("projects.loadError"));
        });
    return () => {
      active = false;
      generation.current += 1;
      useCanvasStore.getState().reset();
    };
  }, [orgId, projectId, positionId, copyId]);

  // Once catalog options arrive, fill uniquely-determined SKUs (coupler when
  // the series has exactly one, mullions for splits created by starters).
  useEffect(() => {
    const product = inputs.product;
    if (!product || !options.data) return;
    const resolved = resolveDefaults(
      product,
      options.data.coupler_skus,
      {
        SPLIT_V: options.data.profiles.find((profile) => profile.role === "MULLION_V")?.sku,
        SPLIT_H: options.data.profiles.find((profile) => profile.role === "MULLION_H")?.sku,
      },
      options.data.glazing_thicknesses.length === 1
        ? options.data.glazing_thicknesses[0]
        : undefined,
      options.data.panel_skus.length === 1 ? options.data.panel_skus[0] : undefined,
    );
    if (resolved !== product) {
      // Deterministic normalization is not a user step: folding it into
      // history would make the preceding change un-undoable.
      useCanvasStore.getState().replaceInputs({ ...inputs, product: resolved });
    }
  }, [inputs, options.data]);

  useEffect(() => {
    function onKey(event: KeyboardEvent): void {
      const target = event.target;
      if (
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target instanceof HTMLSelectElement
      )
        return;
      if (event.key === "Escape") {
        useCanvasStore.getState().select(null);
        return;
      }
      if (event.key === "Delete" || event.key === "Backspace") {
        const state = useCanvasStore.getState();
        const product = state.inputs.product;
        if (
          product !== null &&
          product.assembly.modules.length > 1 &&
          product.assembly.modules.some((module) => module.id === state.selection)
        ) {
          event.preventDefault();
          state.commitInputs({
            ...state.inputs,
            product: removeUnit(product, state.selection),
          });
          state.select(null);
          setResult(null);
          setAssemblyEval(null);
        }
        return;
      }
      if (!(event.ctrlKey || event.metaKey) || event.altKey) return;
      const key = event.key.toLowerCase();
      if (key === "z") {
        event.preventDefault();
        applyHistory(event.shiftKey ? "redo" : "undo");
      } else if (key === "y") {
        event.preventDefault();
        applyHistory("redo");
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  function applyHistory(direction: "undo" | "redo"): void {
    const store = useCanvasStore.getState();
    if (direction === "undo") store.undo();
    else store.redo();
    setResult(null);
    setAssemblyEval(null);
    setMessage("");
  }

  const onAssemblyChanged = useCallback(() => {
    setResult(null);
    setAssemblyEval(null);
    setMessage("");
  }, []);

  useEffect(() => {
    if (createdId === null) return;
    navigate(`/projects/${projectId}/positions/${createdId}/edit`, { replace: true });
  }, [createdId, navigate, projectId]);

  const onAssemblyEvaluation = useCallback((evaluation: EngineAssemblyCalculateResponse | null) => {
    setAssemblyEval(evaluation);
    setResult(
      evaluation?.bom ? { ...evaluation.bom, calculation_hash: evaluation.calculation_hash } : null,
    );
  }, []);

  const assemblyUnsaveable =
    assemblyEval?.status === "INVALID" ||
    (assemblyEval?.modules ?? []).some((module) => module.result == null);

  async function save(): Promise<void> {
    if (
      uncertainCreate ||
      mutationLock.current ||
      !result ||
      assemblyUnsaveable ||
      busy ||
      inputs.color !== "WHITE" ||
      inputs.product === null ||
      !systemId ||
      !/^[1-9]\d*$/.test(quantity) ||
      Number(quantity) > 2147483647
    )
      return;
    mutationLock.current = true;
    const epoch = ++generation.current;
    setBusy(true);
    setMessage("");
    // A lone unit persists in the classic documentary shape; real assemblies
    // save as product-v2. The in-canvas model is always compositional.
    const design = designPayload(inputs) as PositionDesignRequest;
    const body = {
      location_tag: location,
      quantity: Number(quantity),
      design,
    };
    try {
      const response = saved
        ? await positionsUpdate(
            saved.id,
            { ...body, expected_updated_at: saved.updated_at },
            requestOptions,
          )
        : await positionsCreate(projectId, body, requestOptions);
      if (epoch !== generation.current) return;
      if (response.status !== 200 && response.status !== 201)
        throw new ApiError(response.status, response.data);
      const value = response.data as PositionResponse;
      setSaved(value);
      setResult(value.bom);
      setBaseline({ design: canonicalize(design), location, quantity });
      setMessage(t("projects.saved"));
      // The unsaved-changes blocker still sees dirty=true until the baseline
      // commits, so the post-create navigation must wait for the next render.
      if (!positionId) setCreatedId(value.id);
    } catch (error) {
      if (epoch === generation.current) {
        const uncertain = !saved && (!(error instanceof ApiError) || error.status >= 500);
        setUncertainCreate(uncertain);
        setMessage(t(uncertain ? "projects.uncertainPosition" : "projects.saveError"));
      }
    } finally {
      mutationLock.current = false;
      if (epoch === generation.current) setBusy(false);
    }
  }

  if (!loaded) return <p role={message ? "alert" : "status"}>{message || t("projects.loading")}</p>;
  const dirty =
    baseline === null
      ? true
      : canonicalize(designPayload(inputs)) !== baseline.design ||
        location !== baseline.location ||
        quantity !== baseline.quantity;
  const product = inputs.product;
  const pickStarter = (definition: StarterDefinition) => {
    const { widthMm, heightMm } = starterContextSize(product);
    const nextProduct = definition.build(widthMm, heightMm);
    const store = useCanvasStore.getState();
    store.commitInputs({ ...inputs, product: nextProduct });
    // Coupled starters mint fresh module ids — a stale selection would leave
    // the inspector pointed at a module that no longer exists.
    store.select(nextProduct.assembly.modules[0]?.id ?? null);
    setLibraryOpen(false);
    onAssemblyChanged();
  };
  // Position metadata lives in the right inspector column when no element is
  // selected: system/materials is edited in context, not as a permanent form.
  const positionPanel = (
    <section className="assembly-inspector position-panel" aria-label={t("projects.positionData")}>
      <header className="assembly-inspector__header">
        <h4>{t("projects.positionData")}</h4>
      </header>
      <details className="inspector-section" open>
        <summary>{t("projects.identification")}</summary>
        <fieldset disabled={busy}>
          <label className="assembly-field">
            <span>{t("projects.location")}</span>
            <input value={location} onChange={(e) => setLocation(e.target.value)} />
          </label>
          <label className="assembly-field">
            <span>{t("pricing.quantity")}</span>
            <input
              inputMode="numeric"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
            />
          </label>
        </fieldset>
      </details>
      <details className="inspector-section" open>
        <summary>{t("projects.system")}</summary>
        <fieldset disabled={busy}>
          <select
            className="assembly-select"
            aria-label={t("projects.system")}
            value={systemId}
            onChange={(e) => {
              const next = e.target.value || null;
              if (inputs.systemId !== next) {
                useCanvasStore.getState().commitInputs({ ...inputs, systemId: next });
                setMessage("");
              }
            }}
          >
            <option value="">{t("projects.chooseSystem")}</option>
            {systems.data
              ?.filter((system) => system.quote_ready)
              .map((system) => (
                <option key={system.id} value={system.id}>
                  {system.name}
                  {system.is_demo ? ` · ${t("projects.synthetic")}` : ""}
                </option>
              ))}
          </select>
          {(systems.isError || options.isError) && <p role="alert">{t("projects.catalogError")}</p>}
          {(systems.isPending || (systemId && options.isPending)) && (
            <p role="status">{t("projects.loading")}</p>
          )}
          <p className="assembly-hint">{t("projects.colorWhite")}</p>
        </fieldset>
      </details>
    </section>
  );
  return (
    <section className="projects-page position-editor">
      <UnsavedChangesGuard dirty={dirty} message={t("projects.leaveUnsaved")} />
      <header className="projects-header">
        <div>
          <Link to={`/projects/${projectId}`}>{t("projects.back")}</Link>
          <h1>{location || t("projects.position")}</h1>
        </div>
        <span role="status">{dirty ? t("projects.unsaved") : t("projects.savedState")}</span>
        <button disabled={!canUndo || busy} onClick={() => applyHistory("undo")}>
          {t("projects.undo")}
        </button>
        <button disabled={!canRedo || busy} onClick={() => applyHistory("redo")}>
          {t("projects.redo")}
        </button>
        <button
          className="primary-action"
          disabled={uncertainCreate || busy || !result || assemblyUnsaveable}
          onClick={() => void save()}
        >
          {t("projects.save")}
        </button>
      </header>
      {message && <p role="status">{message}</p>}
      <div className="position-workspace">
        <details
          className="starter-library"
          open={libraryOpen}
          onToggle={(event) => setLibraryOpen(event.currentTarget.open)}
        >
          <summary>{t("assembly.starterLibrary")}</summary>
          <StarterGallery
            members={resolveMembers(options.data)}
            disabled={busy}
            onPick={pickStarter}
          />
        </details>
        <AssemblyEditor
          organizationId={orgId}
          couplerSkus={options.data?.coupler_skus ?? []}
          glassSkus={options.data?.glass_skus ?? []}
          panelSkus={options.data?.panel_skus ?? []}
          options={options.data}
          optionsReady={options.data !== undefined || options.isError}
          disabled={busy}
          onChanged={onAssemblyChanged}
          onEvaluationChange={onAssemblyEvaluation}
          positionId={saved?.id ?? null}
          positionPanel={positionPanel}
        />
      </div>
      {result ? (
        <ProjectBom result={result} />
      ) : (
        <p role="status">{t("projects.calculationRequired")}</p>
      )}
    </section>
  );
}

export function ProjectBom({ result }: { result: EngineCalculateResponse }): JSX.Element {
  const longestCut = Math.max(0, ...result.profile_cuts.map((cut) => Number(cut.length_mm)));
  return (
    <details className="project-bom">
      <summary>{t("projects.bom")}</summary>
      <div className="projects-table-scroll">
        <table>
          <thead>
            <tr>
              <th>{t("pricing.profile")}</th>
              <th>{t("projects.length")}</th>
              <th>{t("pricing.quantity")}</th>
            </tr>
          </thead>
          <tbody>
            {result.profile_cuts.map((cut, index) => (
              <tr key={index}>
                <td>{cut.sku}</td>
                <td>
                  {cut.length_mm}
                  <CutBar lengthMm={Number(cut.length_mm)} maxMm={longestCut} />
                </td>
                <td>{cut.qty}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="projects-table-scroll">
        <table>
          <thead>
            <tr>
              <th>{t("pricing.glass")}</th>
              <th>{t("projects.pieceWidth")}</th>
              <th>{t("projects.pieceHeight")}</th>
            </tr>
          </thead>
          <tbody>
            {result.glasses.map((glass, index) => (
              <tr key={index}>
                <td>{index + 1}</td>
                <td>{glass.width_mm}</td>
                <td>{glass.height_mm}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {result.hardware_items.map((kit, index) => (
        <p key={index}>
          {kit.name} × {kit.qty}
        </p>
      ))}
      {(result.fittings ?? []).length > 0 && (
        <div className="projects-table-scroll">
          <table>
            <caption>{t("projects.fittings")}</caption>
            <thead>
              <tr>
                <th>{t("projects.article")}</th>
                <th>{t("assembly.framelessFittings")}</th>
                <th>{t("pricing.quantity")}</th>
              </tr>
            </thead>
            <tbody>
              {(result.fittings ?? []).map((item, index) => (
                <tr key={index}>
                  <td>{item.sku}</td>
                  <td>{item.kind}</td>
                  <td>{item.qty}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {result.reinforcements.length > 0 && (
        <div className="projects-table-scroll">
          <table>
            <caption>{t("projects.reinforcements")}</caption>
            <thead>
              <tr>
                <th>{t("pricing.profile")}</th>
                <th>{t("projects.length")}</th>
                <th>{t("pricing.quantity")}</th>
              </tr>
            </thead>
            <tbody>
              {result.reinforcements.map((item, index) => (
                <tr key={index}>
                  <td>{item.reinforcement_sku || item.parent_profile_sku}</td>
                  <td>
                    {item.length_mm}
                    <CutBar lengthMm={Number(item.length_mm)} maxMm={longestCut} />
                  </td>
                  <td>{item.qty}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {result.panels.length > 0 && (
        <div className="projects-table-scroll">
          <table>
            <caption>{t("projects.panels")}</caption>
            <thead>
              <tr>
                <th>{t("projects.article")}</th>
                <th>{t("projects.pieceWidth")}</th>
                <th>{t("projects.pieceHeight")}</th>
              </tr>
            </thead>
            <tbody>
              {result.panels.map((item, index) => (
                <tr key={index}>
                  <td>{item.name}</td>
                  <td>{item.width_mm}</td>
                  <td>{item.height_mm}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </details>
  );
}

/** Proportional length bar under a cut dimension — reads the cut plan at a
 * glance the way workshop software shows bar vs remnant. */
function CutBar({ lengthMm, maxMm }: { lengthMm: number; maxMm: number }): JSX.Element | null {
  if (!Number.isFinite(lengthMm) || !Number.isFinite(maxMm) || maxMm <= 0 || lengthMm <= 0)
    return null;
  const pct = Math.min(100, Math.max(2, (lengthMm / maxMm) * 100));
  return (
    <span className="cut-bar" aria-hidden="true">
      <span style={{ width: `${pct}%` }} />
    </span>
  );
}
