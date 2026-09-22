import { useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  engineCalculate,
  engineSystems,
  positionsCreate,
  positionsRetrieve,
  positionsUpdate,
  projectDesignOptions,
} from "../../api/generated/dekopen";

import type {
  EngineAssemblyCalculateResponse,
  EngineCalculateResponse,
  PositionResponse,
  NodeLayout,
} from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { ApiError } from "../../api/apiMutator";
import { UnsavedChangesGuard } from "../../app/UnsavedChangesGuard";
import { t } from "../../i18n/es-CL";
import { type CanvasDesignInputs, useCanvasStore } from "../canvas/canvasStore";
import { AssemblyEditor, createBowFromInputs } from "../canvas/AssemblyEditor";
import { IntentEditor } from "../canvas/IntentEditor";
import { FixedPositionPreview } from "./FixedPositionPreview";
import { intentBays, type IntentNode, type SplitType } from "../canvas/intentEditing";
import { isProductModel, totalModuleWidth } from "../canvas/productEditing";
import { requestFromInputs } from "../canvas/useEngineCalculation";

import { useEngineLayout } from "../canvas/useEngineLayout";
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

function initial(): CanvasDesignInputs {
  return {
    systemId: null,
    nominalWidthMm: "1000.00",
    nominalHeightMm: "1000.00",
    color: "WHITE",
    parametricTree: { id: crypto.randomUUID(), type: "BAY", opening_type: "FIXED" },
    product: null,
  };
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
  const [systemId, setSystemId] = useState("");
  const [thickness, setThickness] = useState("");
  const [glassSpec, setGlassSpec] = useState("");
  const [glassSku, setGlassSku] = useState("");
  const [kitSku, setKitSku] = useState("");
  const [pending, setPending] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [intentValidating, setIntentValidating] = useState(false);
  const [intentReady, setIntentReady] = useState(false);
  const [intentDraftPending, setIntentDraftPending] = useState(false);
  const intentValidationLock = useRef(false);
  const mutationLock = useRef(false);
  const [message, setMessage] = useState("");
  const [uncertainCreate, setUncertainCreate] = useState(false);
  const [assemblyEval, setAssemblyEval] = useState<EngineAssemblyCalculateResponse | null>(null);
  const generation = useRef(0);
  const inputs = useCanvasStore((s) => s.inputs);
  const canUndo = useCanvasStore((s) => s.past.length > 0);
  const canRedo = useCanvasStore((s) => s.future.length > 0);

  const layout = useEngineLayout(inputs, orgId);
  const selected = useCanvasStore((s) => s.selection);
  const bay = intentBays(inputs.parametricTree).find((item) => item.id === selected);
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
      useCanvasStore.getState().loadDesign(initial());
      setIntentReady(true);
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
          const product = isProductModel(tree) ? tree : null;
          useCanvasStore.getState().loadDesign({
            systemId: item.design.system_id,
            nominalWidthMm: item.design.nominal_width_mm,
            nominalHeightMm: item.design.nominal_height_mm,

            color: "WHITE",
            parametricTree: product
              ? (product.assembly.modules.at(0)?.tree ??
                ({ id: "m1", type: "BAY", opening_type: "FIXED" } as IntentNode))
              : (tree as IntentNode),
            product,
          });
          setSaved(copyId ? null : item);
          setDirty(!!copyId);
          setSystemId(item.design.system_id);
          setLocation(item.location_tag ?? "");
          setQuantity(String(item.quantity));
          setResult(item.bom);
          setIntentReady(true);
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

  useEffect(() => {
    setThickness(bay?.glass_thickness_mm ?? "");
    setGlassSpec(bay?.glass_spec ?? "");
    setGlassSku(bay?.glass_article_sku ?? "");
    setKitSku(bay?.hardware_set_sku ?? "");
  }, [bay]);

  useEffect(() => {
    function onKey(event: KeyboardEvent): void {
      if (!(event.ctrlKey || event.metaKey) || event.altKey) return;
      const target = event.target;
      if (
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target instanceof HTMLSelectElement
      )
        return;
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
    setDirty(true);
    setMessage("");
  }

  function setProductMode(mode: "single" | "bow"): void {
    const store = useCanvasStore.getState();
    if (mode === "bow" && inputs.product === null) {
      store.commitInputs({
        ...inputs,
        product: createBowFromInputs(inputs, thickness || "4.00", glassSpec || "4"),
      });
    } else if (mode === "single" && inputs.product !== null) {
      store.commitInputs({
        ...inputs,
        product: null,
        parametricTree: inputs.product.assembly.modules.at(0)?.tree ?? inputs.parametricTree,
      });
    } else {
      return;
    }
    setResult(null);
    setAssemblyEval(null);
    setDirty(true);
    setMessage("");
  }

  function editTechnical(): void {
    setPending(true);
    setDirty(true);
    setResult(null);
    setMessage("");
    generation.current += 1;
  }
  function intentValidationChanged(validating: boolean): void {
    intentValidationLock.current = validating;
    setIntentValidating(validating);
    if (validating) {
      generation.current += 1;
      setResult(null);
      setDirty(true);
      setMessage("");
    }
  }
  async function applyMaterials(): Promise<void> {
    if (
      mutationLock.current ||
      intentValidationLock.current ||
      !bay ||
      !systemId ||
      !thickness ||
      !glassSpec.trim()
    )
      return;
    mutationLock.current = true;
    const epoch = ++generation.current;
    setBusy(true);
    setMessage("");
    setResult(null);
    function replace(node: IntentNode): IntentNode {
      if (node.id === selected)
        return {
          ...node,
          glass_thickness_mm: thickness,
          glass_spec: glassSpec,
          glass_article_sku: glassSku || null,
          hardware_set_sku: kitSku || null,
        };
      return { ...node, children: node.children?.map(replace) };
    }
    const candidate = { ...inputs, systemId, parametricTree: replace(inputs.parametricTree) };
    try {
      const response = await engineCalculate(requestFromInputs(candidate), requestOptions);
      if (epoch !== generation.current) return;
      if (response.status !== 200) throw new Error("calculation");
      useCanvasStore.getState().loadDesign(candidate);
      useCanvasStore.getState().selectBay(selected);
      setResult(response.data);
      setIntentReady(true);
      setPending(false);
      setDirty(true);
    } catch {
      if (epoch === generation.current) setMessage(t("intent.rejected"));
    } finally {
      mutationLock.current = false;
      if (epoch === generation.current) setBusy(false);
    }
  }

  async function save(): Promise<void> {
    if (
      uncertainCreate ||
      mutationLock.current ||
      intentValidationLock.current ||
      !result ||
      pending ||
      busy ||
      inputs.color !== "WHITE" ||
      (inputs.product !== null && assemblyEval?.status === "INVALID") ||
      !/^[1-9]\d*$/.test(quantity) ||
      Number(quantity) > 2147483647
    )
      return;
    mutationLock.current = true;
    const epoch = ++generation.current;
    setBusy(true);
    setMessage("");
    const product = inputs.product;
    const design =
      product !== null
        ? {
            system_id: systemId,
            nominal_width_mm: (assemblyEval?.plan
              ? Number(assemblyEval.plan.width_mm)
              : totalModuleWidth(product)
            ).toFixed(2),
            nominal_height_mm: Math.max(
              ...product.assembly.modules.map((module) => Number(module.height_mm)),
            ).toFixed(2),
            color: inputs.color,
            parametric_tree: product,
          }
        : { ...requestFromInputs(inputs), color: inputs.color };
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
      flushSync(() => setDirty(false));
      setMessage(t("projects.saved"));
      if (!positionId)
        navigate(`/projects/${projectId}/positions/${value.id}/edit`, { replace: true });
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

  const mullions: Partial<Record<SplitType, { sku: string; name: string }>> = {};
  for (const article of options.data?.profiles ?? []) {
    if (article.role === "MULLION_V")
      mullions.SPLIT_V = { sku: article.sku, name: t("intent.vertical") };
    if (article.role === "MULLION_H")
      mullions.SPLIT_H = { sku: article.sku, name: t("intent.horizontal") };
  }

  if (!loaded) return <p role={message ? "alert" : "status"}>{message || t("projects.loading")}</p>;
  return (
    <section className="projects-page position-editor">
      <UnsavedChangesGuard dirty={dirty} message={t("projects.leaveUnsaved")} />
      <header className="projects-header">
        <div>
          <Link to={`/projects/${projectId}`}>{t("projects.back")}</Link>
          <h1>{location || t("projects.position")}</h1>
        </div>
        <span role="status">{dirty ? t("projects.unsaved") : t("projects.savedState")}</span>
        <button
          disabled={!canUndo || busy || pending || intentValidating}
          onClick={() => applyHistory("undo")}
        >
          {t("projects.undo")}
        </button>
        <button
          disabled={!canRedo || busy || pending || intentValidating}
          onClick={() => applyHistory("redo")}
        >
          {t("projects.redo")}
        </button>
        <button
          className="primary-action"
          disabled={uncertainCreate || busy || pending || intentValidating || !result}
          onClick={() => void save()}
        >
          {t("projects.save")}
        </button>
      </header>
      {message && <p role="status">{message}</p>}
      <div className="position-workspace">
        <div className="position-design">
          <div className="position-type">
            <label>
              {t("assembly.type")}
              <select
                value={inputs.product === null ? "single" : "bow"}
                disabled={busy || pending || intentValidating}
                onChange={(event) =>
                  setProductMode(event.target.value === "bow" ? "bow" : "single")
                }
              >
                <option value="single">{t("assembly.single")}</option>
                <option value="bow">{t("assembly.bow")}</option>
              </select>
            </label>
          </div>
          {inputs.product === null ? (
            <>
              <FixedPositionPreview inputs={inputs} result={result}>
                <div>
                  <div className="design-caption">{t("projects.distribution")}</div>
                  <DesignDiagram
                    layout={layout}
                    node={inputs.parametricTree}
                    selected={selected}
                    disabled={busy || pending || intentValidating || intentDraftPending}
                    onSelect={(id) => useCanvasStore.getState().selectBay(id)}
                  />
                </div>
              </FixedPositionPreview>
              <IntentEditor
                organizationId={orgId}
                onValidationChange={intentValidationChanged}
                onDraftChange={() => {
                  setIntentDraftPending(true);
                  setDirty(true);
                  setResult(null);
                  setMessage("");
                }}
                disabled={busy || pending || !intentReady}
                mullions={mullions}
                onCalculated={(_, calculated) => {
                  setIntentDraftPending(false);
                  setResult(calculated);
                  setDirty(true);
                  setMessage("");
                }}
              />
            </>
          ) : (
            <AssemblyEditor
              organizationId={orgId}
              couplerSkus={options.data?.coupler_skus ?? []}
              disabled={busy || pending}
              onChanged={() => {
                setDirty(true);
                setMessage("");
              }}
              onEvaluationChange={(evaluation) => {
                setAssemblyEval(evaluation);
                setResult(
                  evaluation?.bom
                    ? {
                        ...evaluation.bom,
                        calculation_hash: evaluation.calculation_hash,
                      }
                    : null,
                );
              }}
            />
          )}
        </div>
        <aside className="position-materials">
          <fieldset disabled={busy || intentValidating || intentDraftPending}>
            <legend>{t("projects.positionData")}</legend>
            <label>
              {t("projects.location")}
              <input
                value={location}
                onChange={(e) => {
                  setLocation(e.target.value);
                  setDirty(true);
                }}
              />
            </label>
            <label>
              {t("pricing.quantity")}
              <input
                inputMode="numeric"
                value={quantity}
                onChange={(e) => {
                  setQuantity(e.target.value);
                  setDirty(true);
                }}
              />
            </label>
            <label>
              {t("projects.system")}
              <select
                value={systemId}
                onChange={(e) => {
                  editTechnical();
                  setSystemId(e.target.value);
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
            </label>
            {(systems.isError || options.isError) && (
              <p role="alert">{t("projects.catalogError")}</p>
            )}
            {(systems.isPending || (systemId && options.isPending)) && (
              <p role="status">{t("projects.loading")}</p>
            )}
            {inputs.product === null && (
              <>
                <label>
                  {t("projects.glassThickness")}
                  <select
                    value={thickness}
                    onChange={(e) => {
                      editTechnical();
                      setThickness(e.target.value);
                    }}
                  >
                    <option value="">{t("projects.chooseGlass")}</option>
                    {options.data?.glazing_thicknesses.map((value) => (
                      <option key={value}>{value}</option>
                    ))}
                  </select>
                </label>
                <label>
                  {t("projects.glassComposition")}
                  <input
                    value={glassSpec}
                    onChange={(e) => {
                      editTechnical();
                      setGlassSpec(e.target.value);
                    }}
                  />
                </label>
                <label>
                  {t("projects.glassArticle")}
                  <select
                    value={glassSku}
                    onChange={(e) => {
                      editTechnical();
                      setGlassSku(e.target.value);
                    }}
                  >
                    <option value="">{t("projects.chooseGlassArticle")}</option>
                    {options.data?.glass_skus.map((sku) => (
                      <option key={sku}>{sku}</option>
                    ))}
                  </select>
                </label>
                <label>
                  {t("projects.hardware")}
                  <select
                    value={kitSku}
                    onChange={(e) => {
                      editTechnical();
                      setKitSku(e.target.value);
                    }}
                  >
                    <option value="">{t("projects.automaticKit")}</option>
                    {options.data?.hardware_kits.map((kit) => (
                      <option key={kit.sku} value={kit.sku}>
                        {kit.name}
                      </option>
                    ))}
                  </select>
                </label>
                <p>{t("projects.colorWhite")}</p>
                <button
                  disabled={!systemId || !thickness || !glassSpec.trim()}
                  onClick={() => void applyMaterials()}
                >
                  {t("projects.calculate")}
                </button>
              </>
            )}
          </fieldset>
        </aside>
      </div>
      {result ? (
        <ProjectBom result={result} />
      ) : (
        <p role="status">{t("projects.calculationRequired")}</p>
      )}
    </section>
  );
}

function DesignDiagram({
  node,

  layout,
  selected,
  onSelect,
  disabled,
}: {
  node: IntentNode;

  layout: NodeLayout[];
  selected: string;
  onSelect(id: string): void;
  disabled: boolean;
}): JSX.Element {
  if (node.type === "ROOT")
    return (
      <>
        {node.children?.map((child) => (
          <DesignDiagram
            layout={layout}
            key={child.id}
            node={child}
            selected={selected}
            onSelect={onSelect}
            disabled={disabled}
          />
        ))}
      </>
    );
  if (node.type === "SPLIT_V" || node.type === "SPLIT_H") {
    const dimensions = layout.find((item) => item.node_id === node.id);
    return (
      <div className={`design-split ${node.type === "SPLIT_H" ? "is-horizontal" : ""}`}>
        {node.children?.map((child, idx) => {
          const style = { flex: dimensions?.child_weights[idx] ?? 1 };
          return (
            <div key={child.id} style={style} className="design-proportional-child">
              <DesignDiagram
                layout={layout}
                node={child}
                selected={selected}
                onSelect={onSelect}
                disabled={disabled}
              />
            </div>
          );
        })}
      </div>
    );
  }
  return (
    <button
      type="button"
      className={`design-bay ${selected === node.id ? "is-selected" : ""}`}
      disabled={disabled}
      aria-pressed={selected === node.id}
      aria-label={t("intent.chooseBay")}
      onClick={() => onSelect(node.id)}
    >
      <svg viewBox="0 0 100 100" aria-hidden="true">
        <rect x="4" y="4" width="92" height="92" />
        {node.opening_type?.includes("RIGHT") && <path d="M92 8 L8 50 L92 92" />}
        {node.opening_type?.includes("LEFT") && <path d="M8 8 L92 50 L8 92" />}
        {(node.opening_type?.startsWith("TILT") || node.opening_type === "AWNING") && (
          <path d="M8 92 L50 8 L92 92" />
        )}
        {node.opening_type === "SLIDING_2L" && (
          <path d="M50 4 V96 M15 50 H40 L33 43 M60 50 H85 L78 57" />
        )}
      </svg>
      <span>{node.glass_spec || t("projects.chooseGlass")}</span>
    </button>
  );
}

export function ProjectBom({ result }: { result: EngineCalculateResponse }): JSX.Element {
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
                <td>{cut.length_mm}</td>
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
                  <td>{item.length_mm}</td>
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
