import { compatibleCouplers } from "../canvas/couplerAuthority";
import { sourcedStarter } from "../canvas/starterAuthority";
import type { DesignOptions, ProjectResponse } from "../../api/generated/models";
import { fmtMm } from "../../format";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
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
  ProfileSystemSummary,
} from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { ApiError } from "../../api/apiMutator";
import { UnsavedChangesGuard } from "../../app/UnsavedChangesGuard";
import { useShellLeaf } from "../../app/shellLeaf";
import { t, tDynamic, tOptional } from "../../i18n/es-CL";
import { domainLabel } from "../../i18n/domainLabels";
import { DeniedState, ErrorState, LoadingState } from "../../ui";
import { Popover } from "../../ui/Overlays";
import { EditorPriceChip } from "../canvas/EditorPriceChip";
import { EditorBottomPanel } from "../canvas/EditorBottomPanel";
import { useEditorMedia } from "../canvas/useEditorLayout";
import { chartFinish } from "../canvas/finishColors";
import { completeFirstPosition } from "../onboarding/draft";
import { type CanvasDesignInputs, useCanvasStore } from "../canvas/canvasStore";
import { useProject } from "./useProject";
import { AssemblyEditor, issueText } from "../canvas/AssemblyEditor";
import { useAssistantSurface } from "../assistant/assistantContext";
import { intentBays } from "../canvas/intentEditing";
import type { IntentNode, Opening } from "../canvas/intentEditing";
import {
  starterContextSize,
  starterNominalSize,
  type StarterDefinition,
} from "../canvas/designLibrary";
import { resolveMembers } from "../canvas/members";
import {
  clearPositionDraft,
  positionDraftKey,
  type PositionDraft,
  readPositionDraft,
  writePositionDraft,
} from "./positionDraft";
import { StarterGallery } from "../canvas/StarterGallery";
import {
  elevationEnvelopeMm,
  isProductModel,
  isSingleUnit,
  wrapTreeAsProduct,
  type ProductJson,
} from "../canvas/productEditing";

import "./projects.css";
import "./editor.css";
import { FinishSelector } from "./FinishSelector";
import { Icon } from "../../ui/Icon";
import { usePresentedOptions } from "../canvas/finishReferences";
import { MeasurementPanel } from "./MeasurementPanel";
import type { MeasurementRecord } from "./mountingModel";
import { mountingGeometryChanged } from "./mountingModel";
import { actionErrorDetail } from "../errors";

/** Why the work's current revision cannot be edited, by cause (server
 * `editable()`: phase ≠ DRAFT, sealed version of the current revision, or
 * applied price). Each cause names its own valid path. */
export function editLockCause(
  project: ProjectResponse | undefined | null,
): { title: string; body: string; action: { label: string; section: string } } | null {
  if (!project) return null;
  if (project.status !== "DRAFT")
    return {
      title: "Revisión emitida: solo lectura",
      body: "Esta cotización ya se emitió. Para cambiar ventanas, crea una revisión sucesora desde Cotización; la revisión emitida se conserva intacta.",
      action: { label: "Ir a Cotización", section: "quote" },
    };
  if (project.versions?.some((version) => version.revision_code === project.current_revision))
    return {
      title: "Revisión sellada: solo lectura",
      body: "La revisión actual quedó sellada al preparar su emisión. Revisa su estado en Cotización o crea una sucesora.",
      action: { label: "Ir a Cotización", section: "quote" },
    };
  if (project.current_pricing_operation_id)
    return {
      title: "Precio aplicado: ventanas bloqueadas",
      body: "El precio de la obra está aplicado y congela el diseño. Para editar, retira el precio borrador en Precio y margen; después vuelve a calcularlo.",
      action: { label: "Ir a Precio y margen", section: "pricing" },
    };
  return null;
}

export function PositionEditorHost({
  projectId,
  positionId,
  copyId,
  creationId,
  preferredSystem,
  presentation,
  onBack,
  onOpenPosition,
  onCreated,
  onOpenSection,
  allowNavigation,
}: {
  projectId: string;
  /** null while creating a new window (or a copy). */
  positionId: string | null;
  copyId: string;
  creationId: string;
  preferredSystem: string | null;
  presentation: "studio" | "expanded" | "hidden";
  onBack(): void;
  onOpenPosition(id: string): void;
  onCreated(id: string): void;
  onOpenSection(section: string): void;
  allowNavigation(next: { pathname: string; search: string }): boolean;
}): JSX.Element {
  const session = useAuthSession();
  const org = session.me?.active_organization;
  const userId = session.me?.user?.id ?? "";
  const canEdit = Boolean(org && ["OWNER", "ESTIMATOR"].includes(org.role));
  // The editor must not mount on a closed revision — the backend's editable()
  // gate would 409 every save, so check BEFORE the canvas store and dirty
  // tracking initialize (review: the «Nuevo vano» dead-end on quoted deals).
  const projectQuery = useProject(canEdit && projectId ? projectId : null);
  if (!canEdit)
    return (
      <DeniedState reason="El dueño o un estimador edita ventanas. Puedes consultar cada ventana desde Mesa de obra." />
    );
  if (projectQuery.isPending) return <LoadingState label="Cargando el proyecto" />;
  if (projectQuery.isError)
    return (
      <ErrorState
        title="No se pudo abrir el proyecto"
        titleAs="h2"
        onRetry={() => void projectQuery.refetch()}
      />
    );
  const lock = editLockCause(projectQuery.data);
  if (lock) {
    return (
      <div className="ui-empty ui-empty--denied editor-lock" role="status">
        <svg className="ui-empty__glyph" aria-hidden="true" viewBox="0 0 16 16">
          <rect x="3" y="7" width="10" height="7" rx="1.5" />
          <path d="M5.5 7V5.5a2.5 2.5 0 0 1 5 0V7" />
        </svg>
        <p className="ui-empty__title">{lock.title}</p>
        <p className="ui-empty__body">{lock.body}</p>
        <div className="ui-empty__action">
          <button
            type="button"
            className="ui-button"
            onClick={() => onOpenSection(lock.action.section)}
          >
            {lock.action.label}
          </button>
          <button type="button" className="ui-button ui-button--ghost" onClick={onBack}>
            Volver a la obra
          </button>
        </div>
      </div>
    );
  }
  return (
    <PositionWorkspace
      key={`${org!.id}:${projectId}:${positionId ?? `create:${creationId}`}:${copyId}`}
      userId={userId}
      orgId={org!.id}
      preferredSystem={preferredSystem}
      projectId={projectId}
      positionId={positionId ?? ""}
      copyId={copyId}
      creationId={creationId}
      presentation={presentation}
      onBack={onBack}
      onOpenPosition={onOpenPosition}
      onCreated={onCreated}
      allowNavigation={allowNavigation}
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
  couplerProfiles: DesignOptions["coupler_profiles"],
  mullionSkus: { SPLIT_V?: string; SPLIT_H?: string },
  glassThicknessMm?: string,
  panelSku?: string,
  glassArticleSku?: string,
): ProductJson {
  let next = product;
  for (const coupling of next.assembly.couplings) {
    const choices = compatibleCouplers(couplerProfiles ?? [], coupling.angle_deg);
    if (choices.length === 1) {
      const sku = choices[0]!.sku;
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
    // A bay can carry thickness/spec without the article (e.g. a pasted spec
    // on a catalog whose glass article was added later) — the select reads the
    // article key, so a missing one leaves phantom glass that eval rejects.
    const missingGlassArticle =
      node.type === "BAY" &&
      !node.glass_article_sku &&
      glassArticleSku !== undefined &&
      ((node.glass_thickness_mm !== null && node.glass_thickness_mm !== undefined) ||
        glassThicknessMm !== undefined);
    const missingPanel =
      node.type === "BAY" &&
      node.opening_type === "DOOR_ENTRY" &&
      !node.panel_article_sku &&
      panelSku !== undefined;
    // A door without declared handedness cannot freeze — manufacturing
    // refuses to guess the hinge side, so autofill declares the default.
    const missingHandedness =
      node.type === "BAY" && node.opening_type === "DOOR_ENTRY" && node.door_handedness == null;
    return (
      missingMullion ||
      missingGlass ||
      missingGlassArticle ||
      missingPanel ||
      missingHandedness ||
      (node.children?.some(needsFill) ?? false)
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
    if (
      updated.type === "BAY" &&
      !updated.glass_article_sku &&
      glassArticleSku !== undefined &&
      updated.glass_thickness_mm
    ) {
      updated = { ...updated, glass_article_sku: glassArticleSku };
    }
    if (updated.type === "BAY" && updated.opening_type === "DOOR_ENTRY" && panelSku !== undefined) {
      if (!updated.panel_article_sku) updated = { ...updated, panel_article_sku: panelSku };
    }
    if (
      updated.type === "BAY" &&
      updated.opening_type === "DOOR_ENTRY" &&
      updated.door_handedness == null
    ) {
      updated = { ...updated, door_handedness: "LEFT" };
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
 * dirty baseline, so they can never disagree about what "unchanged" means.
 * The finish choice is validated against the series' declared colors — never
 * a hardcoded white, and a catalog option the engine can't map stays
 * unsaveable instead of throwing. */
function designPayload(
  inputs: CanvasDesignInputs,
  allowedColors: string[],
): PositionDesignRequest | null {
  const product = inputs.product;
  // The picker's options come from the system's declared finishes — a color
  // outside that set stays displayed and selectable but unsaveable, never
  // silently coerced.
  const color = allowedColors.includes(inputs.color) ? inputs.color : null;
  if (product === null || !inputs.systemId || color === null) return null;
  const single = isSingleUnit(product) ? product.assembly.modules[0] : undefined;
  return single !== undefined
    ? {
        system_id: inputs.systemId,
        nominal_width_mm: single.width_mm,
        nominal_height_mm: single.height_mm,
        color,
        parametric_tree: single.tree,
      }
    : {
        system_id: inputs.systemId,
        nominal_width_mm: elevationEnvelopeMm(product).width.toFixed(2),
        nominal_height_mm: elevationEnvelopeMm(product).height.toFixed(2),
        color,
        parametric_tree: product,
      };
}

/** The unsaved-changes identity — the live inputs themselves, not the
 * save payload: a canvas design with no system picked yet produces no
 * payload at all, and comparing `null` to `null` would call work that
 * doesn't exist yet "unchanged" and let a reload discard it silently. */
function designIdentity(inputs: CanvasDesignInputs): string {
  return canonicalize({
    color: inputs.color,
    nominalHeightMm: inputs.nominalHeightMm,
    nominalWidthMm: inputs.nominalWidthMm,
    product: inputs.product,
    mounting: inputs.mounting ?? [],
    systemId: inputs.systemId,
  });
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

/** Drawing does not require prices or workshop verification. */
function isDrawable(system: Pick<ProfileSystemSummary, "usage" | "quote_ready">): boolean {
  return system.usage
    ? system.usage.levels.some((capability) => capability.level === "DRAWABLE" && capability.ok)
    : system.quote_ready;
}

function isCompanySeries(system: ProfileSystemSummary): boolean {
  return isDrawable(system) && system.is_demo === false;
}

function PositionWorkspace({
  userId,
  orgId,
  projectId,
  positionId,
  copyId,
  creationId,
  preferredSystem,
  presentation,
  onBack,
  onOpenPosition,
  onCreated,
  allowNavigation,
}: {
  userId: string;
  orgId: string;
  projectId: string;
  positionId: string;
  copyId: string;
  creationId: string;
  preferredSystem: string | null;
  presentation: "studio" | "expanded" | "hidden";
  onBack(): void;
  onOpenPosition(id: string): void;
  onCreated(id: string): void;
  allowNavigation(next: { pathname: string; search: string }): boolean;
}): JSX.Element {
  const visible = presentation !== "hidden";
  const readOnly = useEditorMedia("(max-width: 1023px)");
  const [loaded, setLoaded] = useState(false);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [saved, setSaved] = useState<PositionResponse | null>(null);
  const [result, setResult] = useState<EngineCalculateResponse | null>(null);
  const [location, setLocation] = useState("");
  const [quantity, setQuantity] = useState("1");
  // The breadcrumb leaf is the estimator's own tag («Dormitorio») — the
  // shell falls back to «Vano» while the field is blank.
  useShellLeaf(visible ? location.trim() || null : null);
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
  // 409: someone else saved this window. The local edit stays (draft buffer);
  // the person loads the saved version and decides whether to restore.
  const [conflict, setConflict] = useState(false);
  const [assemblyEval, setAssemblyEval] = useState<EngineAssemblyCalculateResponse | null>(null);
  const [calculationState, setCalculationState] = useState<{
    pending: boolean;
    error: string | null;
  }>({ pending: false, error: null });
  const [createdId, setCreatedId] = useState<string | null>(null);
  // Bump when a starter replaces the product — the canvas re-fits even if
  // the user had panned/zoomed the previous drawing away.
  const [viewEpoch, setViewEpoch] = useState(0);
  // Unsaved-draft buffer: a reload used to silently discard the design.
  // A pending draft is offered back explicitly — never auto-applied.
  const draftIdentity = useMemo(
    () => ({
      userId,
      orgId,
      projectId,
      positionId: positionId || null,
      creationId: positionId ? null : `${copyId ? `copy-${copyId}` : "new"}:${creationId}`,
    }),
    [userId, orgId, projectId, positionId, copyId, creationId],
  );
  const draftKey = positionDraftKey(draftIdentity);
  const [pendingDraft, setPendingDraft] = useState<PositionDraft | null>(null);
  // When opened via ?copy=<id>, the source vano's index for the banner that
  // explains what's conserved — the copy is intent, not identity.
  const [copiedFrom, setCopiedFrom] = useState<string | null>(null);
  // New positions open on the design library (the start point); saved ones go
  // straight to the canvas — picking a starter collapses it.
  const [libraryOpen, setLibraryOpen] = useState(!positionId && !copyId);
  const [issuesOpen, setIssuesOpen] = useState(false);
  const project = useProject(projectId);
  const generation = useRef(0);
  const inputs = useCanvasStore((s) => s.inputs);
  const canUndo = useCanvasStore((s) => s.past.length > 0);
  const canRedo = useCanvasStore((s) => s.future.length > 0);
  // The assistant's "this" is the user's current canvas selection — a
  // volatile ref: it reaches the context projection but never keys the
  // durable thread/job (VOLATILE_REFS strips it server-side, and the dock
  // keys threads on stable refs).
  const canvasSelection = useCanvasStore((s) => s.selection);
  useAssistantSurface(
    positionId && visible ? "position" : null,
    positionId
      ? {
          project_id: projectId,
          position_id: positionId,
          ...(canvasSelection ? { selection: canvasSelection } : {}),
        }
      : undefined,
  );
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
  // The company's own sample photos dress the catalog finishes in the drawing
  // (presentation only; codes, price and authority stay with the catalog).
  const presentedOptions = usePresentedOptions(orgId, options.data);
  // Finishes the series declares. A stored finish it stopped offering still
  // displays — the picker lists it once — but can't save: the engine's color
  // contract is the authority, not this list's length.
  const declaredColors = options.data?.colors ?? [];
  const colorChoices =
    inputs.color && !declaredColors.includes(inputs.color)
      ? [...declaredColors, inputs.color]
      : declaredColors;

  useEffect(() => {
    let active = true;
    setMessage("");
    const offerDraftIfDivergent = (
      baselineDesign: string,
      baselineLocation: string,
      baselineQuantity: string,
    ) => {
      const draft = readPositionDraft(draftIdentity);
      if (!draft) return;
      if (
        designIdentity(draft.inputs) !== baselineDesign ||
        draft.location !== baselineLocation ||
        draft.quantity !== baselineQuantity
      )
        setPendingDraft(draft);
      else clearPositionDraft(draftIdentity);
    };
    if (!positionId && !copyId) {
      const blank = initial();
      // A new window starts from the usual values (company → project); the
      // onboarding's explicit ?system= choice still wins.
      const usual = project.data?.effective_design_defaults;
      if (usual?.system_id?.value) blank.systemId = usual.system_id.value;
      if (usual?.color?.value) blank.color = usual.color.value;
      if (preferredSystem) blank.systemId = preferredSystem;
      useCanvasStore.getState().loadDesign(blank);
      const baselineDesign = designIdentity(blank);
      setBaseline({
        design: baselineDesign,
        location: "",
        quantity: "1",
      });
      offerDraftIfDivergent(baselineDesign, "", "1");
      setLoaded(true);
    } else
      void positionsRetrieve(positionId || copyId, { headers: { "X-Organization-ID": orgId } })
        .then((response) => {
          if (!active) return;
          if (response.status !== 200 || response.data.project_id !== projectId)
            throw new Error("unavailable");
          const item = response.data;

          const tree = item.design.parametric_tree;
          const product: ProductJson = isProductModel(tree)
            ? tree
            : wrapTreeAsProduct(
                tree as IntentNode,
                item.design.nominal_width_mm,
                item.design.nominal_height_mm,
              );
          const loadedInputs = {
            systemId: item.design.system_id,
            nominalWidthMm: item.design.nominal_width_mm,
            nominalHeightMm: item.design.nominal_height_mm,
            // A stored finish the series no longer declares still renders —
            // the picker lists it once so the field is honest, while
            // designPayload refuses to save a finish the engine can't map.
            color: item.design.color,
            parametricTree:
              product.assembly.modules.at(0)?.tree ??
              ({ id: "m1", type: "BAY", opening_type: "FIXED" } as IntentNode),
            product,
            mounting: (item.measurements as MeasurementRecord | null | undefined)?.measurements.map(
              (entry) => ({
                ...entry,
                survey: {
                  ...entry.survey,
                  module_id: entry.survey.module_id ?? product.assembly.modules[0]!.id,
                },
              }),
            ),
          };
          useCanvasStore.getState().loadDesign(loadedInputs);
          setCopiedFrom(copyId ? `P${item.position_index}` : null);
          setSaved(copyId ? null : item);
          setBaseline(
            copyId
              ? null
              : {
                  design: designIdentity(loadedInputs),
                  location: item.location_tag ?? "",
                  quantity: String(item.quantity),
                },
          );
          offerDraftIfDivergent(
            designIdentity(loadedInputs),
            item.location_tag ?? "",
            String(item.quantity),
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
  }, [orgId, projectId, positionId, copyId, preferredSystem, draftKey, loadAttempt]);

  // Once catalog options arrive, fill uniquely-determined SKUs (coupler when
  // the series has exactly one, mullions for splits created by starters).
  useEffect(() => {
    const product = inputs.product;
    if (!product || !options.data) return;
    // The usual glass fills empty bays when the series accepts it; otherwise
    // only a uniquely determined catalog value is filled.
    const usualSku = project.data?.effective_design_defaults?.glass_article_sku?.value;
    const usualGlass = usualSku
      ? options.data.glass_specs.find(
          (glass) => glass.sku === usualSku && glass.compatible !== false,
        )
      : undefined;
    const usualThickness =
      usualGlass?.total_thickness_mm &&
      options.data.glazing_thicknesses.includes(usualGlass.total_thickness_mm)
        ? usualGlass.total_thickness_mm
        : undefined;
    const resolved = resolveDefaults(
      product,
      options.data.coupler_profiles,
      {
        SPLIT_V: options.data.profiles.find((profile) => profile.role === "MULLION_V")?.sku,
        SPLIT_H: options.data.profiles.find((profile) => profile.role === "MULLION_H")?.sku,
      },
      usualThickness ??
        (options.data.glazing_thicknesses.length === 1
          ? options.data.glazing_thicknesses[0]
          : undefined),
      options.data.panel_skus.length === 1 ? options.data.panel_skus[0] : undefined,
      usualThickness && usualGlass
        ? usualGlass.sku
        : options.data.glass_skus.length === 1
          ? options.data.glass_skus[0]
          : undefined,
    );
    if (resolved !== product) {
      // Deterministic normalization is not a user step: folding it into
      // history would make the preceding change un-undoable.
      useCanvasStore.getState().replaceInputs({ ...inputs, product: resolved });
    }
  }, [inputs, options.data, project.data?.effective_design_defaults]);

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
    onCreated(createdId);
  }, [createdId, onCreated]);

  const onAssemblyEvaluation = useCallback(
    (
      evaluation: EngineAssemblyCalculateResponse | null,
      state?: { pending: boolean; error: string | null },
    ) => {
      setAssemblyEval(evaluation);
      if (state) setCalculationState(state);
      setResult(
        evaluation?.bom
          ? { ...evaluation.bom, calculation_hash: evaluation.calculation_hash }
          : null,
      );
    },
    [],
  );

  // designIdentity deep-serializes the product — memoize on the inputs
  // reference so location/quantity keystrokes skip the canonicalization.
  const identity = useMemo(() => designIdentity(inputs), [inputs]);

  const isDirty =
    baseline === null
      ? true
      : identity !== baseline.design ||
        location !== baseline.location ||
        quantity !== baseline.quantity;

  // Debounced draft write — clears once the design matches the saved state
  // again (including right after a successful save).
  useEffect(() => {
    if (!loaded) return;
    if (!isDirty) {
      clearPositionDraft(draftIdentity);
      return;
    }
    const timer = setTimeout(
      () =>
        writePositionDraft(draftIdentity, {
          inputs,
          location,
          quantity,
          savedAt: Date.now(),
          baseline: baseline?.design ?? null,
          revision: project.data?.current_revision ?? null,
        }),
      600,
    );
    return () => clearTimeout(timer);
  }, [
    loaded,
    isDirty,
    identity,
    location,
    quantity,
    draftKey,
    draftIdentity,
    inputs,
    baseline,
    project.data?.current_revision,
  ]);

  const assemblyUnsaveable =
    assemblyEval?.status === "INVALID" ||
    (assemblyEval?.modules ?? []).some((module) => module.result == null);
  // Only flag once the options payload actually arrived — an empty declared
  // list pre-load is "unknown", not "undeclared".
  const colorUndeclared =
    options.data !== undefined && inputs.color !== null && !declaredColors.includes(inputs.color);
  const quantityInvalid = !/^[1-9]\d*$/.test(quantity) || Number(quantity) > 2147483647;
  const mountingChanged = mountingGeometryChanged(inputs.product, inputs.mounting);
  // Local, cheap check: a bay with neither glass nor panel fill can never
  // evaluate — name it so the disabled Guardar isn't a silent dead end.
  const fillUnassigned = (inputs.product?.assembly.modules ?? []).some((module) =>
    intentBays(module.tree).some((bay) => !bay.glass_spec && !bay.panel_article_sku),
  );
  // A disabled Guardar must name the first real blocker ("la hoja queda bajo
  // el ancho mínimo del herraje"), not a generic "revisa los parámetros".
  const saveBlockReason = mountingChanged
    ? "La fabricación cambió: recalcula y aplica Vano y montaje antes de guardar."
    : quantityInvalid
      ? t("projects.qtyInvalid")
      : colorUndeclared
        ? t("projects.colorNotDeclared")
        : fillUnassigned
          ? t("projects.glazingMissing")
          : assemblyUnsaveable && assemblyEval !== null && assemblyEval.issues.length > 0
            ? issueText(
                assemblyEval.issues[0]!,
                inputs.product?.assembly.modules ?? [],
                inputs.product?.assembly.couplings ?? [],
              )
            : null;

  async function save(): Promise<boolean> {
    if (
      uncertainCreate ||
      readOnly ||
      mutationLock.current ||
      !result ||
      assemblyUnsaveable ||
      fillUnassigned ||
      mountingChanged ||
      busy ||
      !options.data ||
      !declaredColors.includes(inputs.color) ||
      inputs.product === null ||
      !systemId ||
      !/^[1-9]\d*$/.test(quantity) ||
      Number(quantity) > 2147483647
    )
      return false;
    mutationLock.current = true;
    const epoch = ++generation.current;
    setBusy(true);
    setMessage("");
    // A lone unit persists in the classic documentary shape; real assemblies
    // save as product-v2. The in-canvas model is always compositional.
    const design = designPayload(inputs, declaredColors) as PositionDesignRequest;
    const body = {
      location_tag: location,
      quantity: Number(quantity),
      design,
      ...(inputs.mounting?.length
        ? {
            measurements: inputs.mounting.map((entry) => ({
              ...entry.survey,
              module_id: isSingleUnit(inputs.product!) ? null : entry.survey.module_id,
            })),
          }
        : {}),
    };
    try {
      const response = saved
        ? await positionsUpdate(
            saved.id,
            { ...body, expected_updated_at: saved.updated_at },
            requestOptions,
          )
        : await positionsCreate(projectId, body, requestOptions);
      if (epoch !== generation.current) return false;
      if (response.status !== 200 && response.status !== 201)
        throw new ApiError(response.status, response.data);
      const value = response.data as PositionResponse;
      completeFirstPosition(orgId, projectId);
      setSaved(value);
      setResult(value.bom);
      setBaseline({ design: designIdentity(inputs), location, quantity });
      setMessage(t("projects.saved"));
      // The unsaved-changes blocker still sees dirty=true until the baseline
      // commits, so the post-create navigation must wait for the next render.
      if (!positionId) setCreatedId(value.id);
      return true;
    } catch (error) {
      if (epoch === generation.current) {
        const uncertain = !saved && (!(error instanceof ApiError) || error.status >= 500);
        setUncertainCreate(uncertain);
        if (saved && error instanceof ApiError && error.status === 409) {
          // Keep the edit in the draft buffer before anything reloads.
          writePositionDraft(draftIdentity, {
            inputs,
            location,
            quantity,
            savedAt: Date.now(),
            baseline: baseline?.design ?? null,
            revision: project.data?.current_revision ?? null,
          });
          setConflict(true);
        }
        setMessage(
          uncertain
            ? t("projects.uncertainPosition")
            : actionErrorDetail(error, t("projects.saveError")),
        );
      }
      return false;
    } finally {
      mutationLock.current = false;
      if (epoch === generation.current) setBusy(false);
    }
  }

  // Ctrl/⌘+S saves the position — without it the chord hits the browser's
  // save-page dialog mid-edit. The ref keeps the listener on the freshest
  // closure (save reads live state).
  const saveRef = useRef(save);
  saveRef.current = save;
  useEffect(() => {
    if (!visible) return;
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        if (!readOnly) void saveRef.current();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [visible, readOnly]);

  if (!loaded)
    return message ? (
      <ErrorState
        title="No se pudo abrir la posición"
        titleAs="h1"
        body="No se recibió el diseño guardado. Vuelve a consultar para abrir esta posición."
        onRetry={() => setLoadAttempt((attempt) => attempt + 1)}
      />
    ) : (
      <LoadingState label="Cargando la posición" />
    );
  const dirty = isDirty;
  const restoreDraft = (draft: PositionDraft) => {
    const store = useCanvasStore.getState();
    store.loadDesign(draft.inputs);
    setLocation(draft.location);
    setQuantity(draft.quantity);
    setLibraryOpen(false);
    setViewEpoch((epoch) => epoch + 1);
    setPendingDraft(null);
    setMessage("");
  };
  const product = inputs.product;
  const pickStarter = (definition: StarterDefinition) => {
    const { widthMm, heightMm } = starterContextSize(product);
    // The library card previews the starter at its nominal size — building
    // it smaller than that can land a leaf under the hardware minimum (a
    // 1000 mm "Dos hojas" makes two ~440 mm sashes). Floor at nominal so a
    // starter always produces what its thumbnail promised.
    const nominal = definition.nominal ?? starterNominalSize(definition.key);
    const nextProduct = sourcedStarter(
      definition.build(
        definition.recipeCode ? nominal.widthMm : Math.max(widthMm, nominal.widthMm),
        definition.recipeCode ? nominal.heightMm : Math.max(heightMm, nominal.heightMm),
      ),
      options.data,
    );
    const store = useCanvasStore.getState();
    store.commitInputs({ ...inputs, product: nextProduct });
    // Coupled starters mint fresh module ids — a stale selection would leave
    // the inspector pointed at a module that no longer exists.
    store.select(nextProduct.assembly.modules[0]?.id ?? null);
    setViewEpoch((epoch) => epoch + 1);
    setLibraryOpen(false);
    onAssemblyChanged();
  };
  // Position facts accompany an unselected drawing.
  const systemName = systems.data?.find((system) => system.id === inputs.systemId)?.name ?? "—";
  const finish = options.data?.finish_authority
    ? chartFinish(options.data.finish_authority, inputs.color)
    : null;
  const finishName = finish
    ? finish.interior.name === finish.exterior.name
      ? finish.interior.name
      : `${finish.interior.name} / ${finish.exterior.name}`
    : declaredColors.includes(inputs.color)
      ? tDynamic("projects.color", inputs.color)
      : "Sin dato";
  const positionPanel = (
    <section className="assembly-inspector position-panel" aria-label={t("projects.positionData")}>
      <header className="assembly-inspector__header">
        <h4>{t("projects.positionData")}</h4>
      </header>
      <dl className="inspector-summary__list">
        <div className="inspector-summary__row">
          <dt>{t("projects.location")}</dt>
          <dd>{location.trim() || "—"}</dd>
        </div>
        <div className="inspector-summary__row">
          <dt>{t("pricing.quantity")}</dt>
          <dd>{quantity || "1"}</dd>
        </div>
        <div className="inspector-summary__row">
          <dt>{t("projects.system")}</dt>
          <dd>{systemName}</dd>
        </div>
      </dl>
    </section>
  );
  function chooseSystem(next: string | null): void {
    if (inputs.systemId === next) return;
    useCanvasStore.getState().commitInputs({ ...inputs, systemId: next });
    setMessage("");
    onAssemblyChanged();
  }
  return (
    <section
      className={`projects-page position-editor position-editor--${presentation}`}
      hidden={!visible}
    >
      <UnsavedChangesGuard
        dirty={dirty}
        message="Esta ventana tiene cambios sin guardar"
        allow={allowNavigation}
        onSave={() => saveRef.current()}
        onDiscard={() => clearPositionDraft(draftIdentity)}
      />
      <header className="position-strip">
        <h2 className="visually-hidden">{location || t("projects.position")}</h2>
        <button
          type="button"
          className="editor-project-link"
          aria-label={presentation === "studio" ? "Volver a Mesa de obra" : "Volver a la obra"}
          title={project.data?.name ?? t("projects.back")}
          onClick={onBack}
        >
          <Icon name="chevronLeft" size={20} />
        </button>
        <input
          className="editor-location"
          aria-label={t("projects.location")}
          placeholder="Nombre o ubicación · p. ej. Dormitorio"
          value={location}
          disabled={busy || readOnly}
          onChange={(e) => setLocation(e.target.value)}
        />
        <label className="editor-quantity">
          <span>Cant.</span>
          <input
            inputMode="numeric"
            aria-label={t("pricing.quantity")}
            value={quantity}
            disabled={busy || readOnly}
            onChange={(e) => setQuantity(e.target.value)}
            aria-invalid={quantityInvalid || undefined}
          />
        </label>
        <Popover
          label="Serie de perfiles"
          trigger={
            <button type="button" className="editor-chip editor-system-chip" title={systemName}>
              <Icon name="catalogs" size={16} />
              {systemId ? systemName : "Elegir serie"}
            </button>
          }
        >
          <label className="editor-system-field">
            <span>{t("projects.system")}</span>
            <select
              className="assembly-select"
              aria-label={t("projects.system")}
              disabled={busy || readOnly}
              value={systemId}
              onChange={(e) => chooseSystem(e.target.value || null)}
            >
              <option value="">{t("projects.chooseSystem")}</option>
              {systemId &&
                systems.data &&
                !systems.data.some((system) => system.id === systemId && isDrawable(system)) && (
                  <option value={systemId}>
                    Catálogo histórico del producto{options.data?.is_demo ? " · DEMO" : ""}
                  </option>
                )}
              {systems.data?.some(isCompanySeries) ? (
                <optgroup label="Series de la empresa">
                  {systems.data?.filter(isCompanySeries).map((system) => (
                    <option key={system.id} value={system.id}>
                      {system.name}
                    </option>
                  ))}
                </optgroup>
              ) : null}
              {systems.data?.some((system) => isDrawable(system) && system.is_demo) ? (
                <optgroup label="Laboratorio · DEMO sintético, sin certificación">
                  {systems.data
                    ?.filter((system) => isDrawable(system) && system.is_demo)
                    .map((system) => (
                      <option key={system.id} value={system.id}>
                        {system.name.replace(/\s*·\s*DEMO\s*$/u, "")} · DEMO
                      </option>
                    ))}
                </optgroup>
              ) : null}
            </select>
          </label>
          {(systems.isError || options.isError) && (
            <p className="editor-catalog-status" role="alert">
              {t("projects.catalogError")}
              <button
                type="button"
                onClick={() => {
                  void systems.refetch();
                  if (systemId) void options.refetch();
                }}
              >
                Reintentar catálogo
              </button>
            </p>
          )}
          {(systems.isPending || (systemId && options.isPending)) && (
            <p className="editor-catalog-status" role="status">
              {t("projects.loading")}
            </p>
          )}
        </Popover>
        <Popover
          label="Acabado"
          trigger={
            <button
              type="button"
              className="editor-chip"
              title={finishName}
              aria-label={`Acabado: ${finishName}`}
            >
              <Icon name="swatch" size={16} />
              {finishName}
            </button>
          }
        >
          {!options.data?.finish_authority && (
            <label className="editor-system-field">
              <span>{t("projects.color")}</span>
              <select
                className="assembly-select"
                aria-label={t("projects.color")}
                disabled={busy || readOnly || declaredColors.length === 0}
                value={inputs.color}
                onChange={(event) =>
                  useCanvasStore.getState().commitInputs({
                    ...inputs,
                    color: event.target.value as CanvasDesignInputs["color"],
                  })
                }
              >
                {colorChoices.length === 0 && <option value={inputs.color}>{inputs.color}</option>}
                {colorChoices.map((color) => (
                  <option key={color} value={color}>
                    {tDynamic("projects.color", color)}
                  </option>
                ))}
              </select>
            </label>
          )}
          {options.data?.finish_authority && (
            <FinishSelector
              authority={presentedOptions?.finish_authority ?? options.data.finish_authority}
              value={inputs.color}
              design={designPayload(inputs, declaredColors)}
              organizationId={orgId}
              disabled={busy || readOnly}
              onChange={(color) => useCanvasStore.getState().commitInputs({ ...inputs, color })}
            />
          )}
        </Popover>
        <span className="editor-save-state" role="status">
          {busy
            ? "Guardando…"
            : dirty
              ? t("projects.unsaved")
              : saved === null
                ? t("projects.draft")
                : t("projects.savedState")}
        </span>
        <button
          type="button"
          className="editor-history"
          aria-label={t("projects.undo")}
          title="Deshacer · Ctrl+Z"
          disabled={!canUndo || busy || readOnly}
          onClick={() => applyHistory("undo")}
        >
          <Icon name="undo" />
        </button>
        <button
          type="button"
          className="editor-history"
          aria-label={t("projects.redo")}
          title="Rehacer · Ctrl+Y"
          disabled={!canRedo || busy || readOnly}
          onClick={() => applyHistory("redo")}
        >
          <Icon name="redo" />
        </button>
        {systemId ? (
          <>
            <EditorPriceChip
              organizationId={orgId}
              inputs={inputs}
              quantity={quantity}
              pending={calculationState.pending}
              ready={Boolean(
                result &&
                options.data &&
                !assemblyUnsaveable &&
                !quantityInvalid &&
                !colorUndeclared,
              )}
            />
            <button
              type="button"
              className="editor-chip editor-verdict"
              aria-expanded={issuesOpen}
              aria-controls="editor-missing"
              title="Revisar qué falta"
              onClick={() => setIssuesOpen((open) => !open)}
            >
              {systems.isError || options.isError || calculationState.error
                ? "Error de cálculo"
                : saveBlockReason
                  ? "Bloqueado"
                  : !assemblyEval || calculationState.pending
                    ? "Calculando…"
                    : assemblyUnsaveable
                      ? "Bloqueado"
                      : assemblyEval.issues.length
                        ? `${assemblyEval.issues.length} avisos`
                        : "Válido"}
            </button>
          </>
        ) : null}
        <button
          type="button"
          className="ui-button ui-button--primary editor-save"
          disabled={
            readOnly ||
            uncertainCreate ||
            busy ||
            !result ||
            !options.data ||
            assemblyUnsaveable ||
            fillUnassigned ||
            mountingChanged ||
            quantityInvalid ||
            colorUndeclared
          }
          title={
            saveBlockReason !== null
              ? `${t("projects.saveBlocked")}: ${saveBlockReason}`
              : !result || assemblyUnsaveable
                ? t("projects.saveBlocked")
                : `${t("projects.save")} (Ctrl+S)`
          }
          onClick={() => void save()}
        >
          {t("projects.save")}
        </button>
      </header>
      {readOnly && (
        <p className="editor-readonly" role="status">
          Vista de lectura · edición disponible desde 1024 px.
        </p>
      )}
      {message && (
        <output className="editor-message" role="status">
          {message}
        </output>
      )}
      {conflict && (
        <div className="draft-banner" role="alert">
          <span>
            Otra persona guardó esta ventana después de que la abriste. Tus cambios siguen aquí y en
            el borrador de esta pestaña; no se enviaron.
          </span>
          <button
            type="button"
            onClick={() => {
              setConflict(false);
              setMessage("");
              setLoadAttempt((attempt) => attempt + 1);
            }}
          >
            Cargar la versión guardada
          </button>
        </div>
      )}
      {copyId && loaded && copiedFrom && (
        <div className="draft-banner" role="status">
          <span>{t("projects.copyNotice").replace("{src}", copiedFrom)}</span>
        </div>
      )}
      {pendingDraft !== null && (
        <div className="draft-banner" role="status">
          <span>
            {t("projects.draftFound").replace(
              "{time}",
              new Date(pendingDraft.savedAt).toLocaleString("es-CL", {
                dateStyle: "short",
                timeStyle: "short",
              }),
            )}
          </span>
          {pendingDraft.baseline && baseline && pendingDraft.baseline !== baseline.design ? (
            <span className="draft-banner__warn">
              Se tomó sobre otra versión guardada de esta ventana: al restaurarlo reemplaza la
              versión actual en el editor (sin guardar) y se vuelve a calcular.
            </span>
          ) : null}
          <button type="button" onClick={() => restoreDraft(pendingDraft)}>
            {t("projects.restoreDraft")}
          </button>
          <button
            type="button"
            onClick={() => {
              clearPositionDraft(draftIdentity);
              setPendingDraft(null);
            }}
          >
            {t("projects.discardDraft")}
          </button>
        </div>
      )}
      <div className="position-body">
        <div className="position-workspace" role="region" aria-labelledby="position-design-title">
          <h2 id="position-design-title" className="visually-hidden">
            Diseño de la posición
          </h2>
          <AssemblyEditor
            organizationId={orgId}
            couplerSkus={options.data?.coupler_skus ?? []}
            glassSkus={options.data?.glass_skus ?? []}
            panelSkus={options.data?.panel_skus ?? []}
            options={presentedOptions}
            optionsReady={options.data !== undefined || options.isError}
            disabled={busy || readOnly}
            quantity={quantityInvalid ? 1 : Number(quantity)}
            libraryOpen={libraryOpen}
            onLibraryToggle={() => setLibraryOpen((open) => !open)}
            libraryTitle={systemId ? "Biblioteca de tipologías" : "¿Con qué serie la fabricas?"}
            library={
              options.isError ? (
                <ErrorState
                  title="No se pudo cargar la biblioteca"
                  onRetry={() => void options.refetch()}
                />
              ) : systemId.length === 0 ? (
                <SeriesChooser
                  systems={systems.data}
                  failed={systems.isError}
                  disabled={busy || readOnly}
                  onRetry={() => void systems.refetch()}
                  onPick={chooseSystem}
                />
              ) : options.data === undefined ? (
                <LoadingState label="Cargando las tipologías compatibles" />
              ) : (
                <StarterGallery
                  options={options.data}
                  allowedOpenings={
                    options.data.system_family ? options.data.compatible_openings : undefined
                  }
                  members={resolveMembers(options.data)}
                  disabled={busy || readOnly}
                  onPick={pickStarter}
                />
              )
            }
            issuesOpen={issuesOpen}
            onCloseIssues={() => setIssuesOpen(false)}
            onOpenIssues={() => setIssuesOpen(true)}
            saveBlockReason={saveBlockReason}
            onChooseSystem={() =>
              document.querySelector<HTMLButtonElement>(".editor-system-chip")?.click()
            }
            onChanged={onAssemblyChanged}
            onEvaluationChange={onAssemblyEvaluation}
            positionId={saved?.id ?? null}
            positionPanel={positionPanel}
            contentEpoch={viewEpoch}
          />
        </div>
      </div>
      <footer className="editor-bottom">
        {presentation === "expanded" ? (
          <EditorBottomPanel title="Ventanas de la obra">
            <nav className="editor-position-list" aria-label="Ventanas de la obra">
              {project.data?.positions?.map((item) => (
                <button
                  type="button"
                  key={item.id}
                  aria-current={item.id === positionId ? "page" : undefined}
                  onClick={() => onOpenPosition(item.id)}
                >
                  {item.location_tag || `Ventana ${item.position_index}`}
                </button>
              ))}
              <Link to={`/projects/${projectId}/positions/new`}>
                <Icon name="plus" size={16} /> Agregar ventana
              </Link>
            </nav>
          </EditorBottomPanel>
        ) : null}
        {saved && (
          <EditorBottomPanel title="Medidas para producción">
            <MeasurementPanel
              position={saved}
              orgId={orgId}
              canConfirm={!readOnly}
              dirty={isDirty}
              onSaved={() =>
                void positionsRetrieve(saved.id, requestOptions).then((r) => {
                  if (r.status === 200) setSaved(r.data);
                })
              }
            />
          </EditorBottomPanel>
        )}
        {result ? (
          <ProjectBom result={result} floating />
        ) : (
          <span>{t("projects.calculationRequired")}</span>
        )}
      </footer>
    </section>
  );
}

export function ProjectBom({
  result,
  floating = false,
}: {
  result: EngineCalculateResponse;
  floating?: boolean;
}): JSX.Element {
  const longestCut = Math.max(0, ...result.profile_cuts.map((cut) => Number(cut.length_mm)));
  const content = (
    <div className="project-bom-content">
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
                  {fmtMm(cut.length_mm)}
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
                <td>{fmtMm(glass.width_mm)}</td>
                <td>{fmtMm(glass.height_mm)}</td>
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
                  <td>
                    {tOptional(`assembly.fittingKind.${item.kind}`) ?? domainLabel(item.kind)}
                  </td>
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
                    {fmtMm(item.length_mm)}
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
                  <td>{fmtMm(item.width_mm)}</td>
                  <td>{fmtMm(item.height_mm)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
  return floating ? (
    <EditorBottomPanel title={t("projects.bom")}>{content}</EditorBottomPanel>
  ) : (
    <details className="project-bom">
      <summary>{t("projects.bom")}</summary>
      {content}
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

type SeriesSummary = { id: string; code: string; name: string; system_family: string | null };

/** First decision of a new window: the series, picked in one click from the
 * same drawable list the strip offers (company first, DEMO apart). */
function SeriesChooser({
  systems,
  failed,
  disabled,
  onRetry,
  onPick,
}: {
  systems?: ProfileSystemSummary[];
  failed: boolean;
  disabled: boolean;
  onRetry(): void;
  onPick(systemId: string): void;
}): JSX.Element {
  if (failed) return <ErrorState title="No se pudieron cargar las series" onRetry={onRetry} />;
  if (systems === undefined) return <LoadingState label="Cargando las series" />;
  const company = systems.filter(isCompanySeries);
  const lab = systems.filter((system) => isDrawable(system) && system.is_demo);
  if (company.length + lab.length === 0)
    return (
      <p className="series-chooser__empty">
        Completa los perfiles de una serie para empezar a dibujar en{" "}
        <Link to="/catalogs/systems">Catálogo</Link>.
      </p>
    );
  const group = (title: string, items: SeriesSummary[], demo: boolean): JSX.Element | null =>
    items.length ? (
      <section className="series-chooser__group" aria-label={title}>
        <h3>{title}</h3>
        <ul>
          {items.map((system) => (
            <li key={system.id}>
              <button
                type="button"
                className="series-chooser__option"
                disabled={disabled}
                onClick={() => onPick(system.id)}
              >
                <span className="series-chooser__name">
                  {system.name.replace(/\s*·\s*DEMO\s*$/u, "")}
                </span>
                <span className="series-chooser__meta">
                  {[
                    system.system_family ? domainLabel(system.system_family) : null,
                    demo ? "DEMO" : null,
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                </span>
                <Icon name="chevronRight" size={16} />
              </button>
            </li>
          ))}
        </ul>
      </section>
    ) : null;
  return (
    <div className="series-chooser">
      <p className="series-chooser__lead">
        La serie define perfiles, aperturas y vidrios posibles. Puedes cambiarla después.
      </p>
      {group("Series de la empresa", company, false)}
      {group("Laboratorio · DEMO sin certificación", lab, true)}
    </div>
  );
}
