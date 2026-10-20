import {
  Component,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { Canvas } from "@react-three/fiber";
import type { PlanGeometry } from "../../api/generated/models";
import type { ProductJson } from "./productEditing";
import type { MemberGeometry } from "./members";
import type { OpeningLeafFact } from "./physicalOpenings";
import { buildScene3D, type LeafMotion, type ModuleScene } from "./Product3DScene";
import { Model3DStage } from "./Model3DStage";
import type { MaterialMode } from "./materials3d";
import type { LeafPoseMode, LeafPoseState } from "./poses3d";
import { STUDIO_TONE_MAPPING, type CameraPreset } from "./studioRig3d";
import { webglAvailable } from "./webglAvailable";
import { Icon } from "../../ui/Icon";
import { finishTextureAvailable, prepareFinishTextures } from "./finishMaterials3d";

const NOOP = () => {};
const EMPTY_FACTS: Record<string, OpeningLeafFact[]> = {};
type States = Record<string, Record<string, LeafPoseState>>;
class RenderBoundary extends Component<
  { children: ReactNode; onError(): void },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch() {
    this.props.onError();
  }
  render() {
    return this.state.failed ? null : this.props.children;
  }
}

/** Controls only change presentation, never intent, BOM or documentary authority. */
export default function Model3DView({
  product,
  members,
  plan,
  openingFacts = EMPTY_FACTS,
  selection = null,
  onSelectModule = NOOP,
  onSelectBay = NOOP,
  onSelectCoupling = NOOP,
  audience = "office",
}: {
  product: ProductJson;
  members: MemberGeometry;
  plan?: PlanGeometry | null;
  openingFacts?: Record<string, OpeningLeafFact[]>;
  selection?: string | null;
  onSelectModule?(moduleId: string): void;
  onSelectBay?(moduleId: string, bayId: string): void;
  onSelectCoupling?(couplingId: string): void;
  audience?: "office" | "portal";
}): JSX.Element {
  const [mode, setMode] = useState<MaterialMode>("commercial");
  const [preset, setPreset] = useState<CameraPreset>(
    members.viewFace === "exterior" ? "exterior" : "interior",
  );
  const [states, setStates] = useState<States>({});
  const [clip, setClip] = useState(false),
    [explode, setExplode] = useState(false),
    [wall, setWall] = useState(false);
  const [error, setError] = useState(false),
    [attempt, setAttempt] = useState(0),
    [exportReady, setExportReady] = useState(false);
  const capture = useRef<(() => string) | null>(null);
  const [, setTextureEpoch] = useState(0);
  useEffect(() => {
    let alive = true;
    void prepareFinishTextures(members.finish).then(() => {
      if (alive) setTextureEpoch((value) => value + 1);
    });
    return () => {
      alive = false;
    };
  }, [members.finish]);
  const scene = useMemo(
    () => buildScene3D(product, members, plan, openingFacts),
    [product, members, plan, openingFacts],
  );
  const hasLeaves = scene.modules.some((module) => module.leaves.length > 0);
  const schematicHardware = scene.modules.some((module) =>
    module.solids.some((solid) => solid.approximate && ["handle", "hinge"].includes(solid.surface)),
  );
  const approximate = scene.modules.some((module) =>
    module.solids.some((solid) => solid.approximate && ["frame", "sash"].includes(solid.surface)),
  );
  const finishes = members.finish ? [members.finish.interior, members.finish.exterior] : [];
  const approximateColor =
    finishes.length === 0 ||
    finishes.some(
      (finish) =>
        finish.approximate ||
        (finish.kind === "FOIL" &&
          (!finish.texture_path || !finishTextureAvailable(finish.texture_path))),
    );
  const onError = useCallback(() => setError(true), []);
  const onExport = useCallback((fn: () => string) => {
    capture.current = fn;
    setExportReady(true);
  }, []);
  const pick = (owner: string) => {
    const split = owner.indexOf("/");
    if (split > 0) onSelectBay(owner.slice(0, split), owner.slice(split + 1));
    else if (product.assembly.modules.some((module) => module.id === owner)) onSelectModule(owner);
    else onSelectCoupling(owner);
  };
  const changeLeaf = (module: ModuleScene, leaf: LeafMotion, pose: LeafPoseMode) => {
    setExplode(false);
    setStates((previous) => {
      const current = { ...previous[module.moduleId] };
      const existing = current[leaf.leafId];
      const target = existing?.mode === pose && existing.amount > 0 ? 0 : 1;
      const group = leaf.fact?.advanced?.fold_group;
      if (group && pose !== "pass") {
        for (const sibling of module.leaves.filter(
          (candidate) =>
            candidate.fact?.bay_id === leaf.fact!.bay_id &&
            candidate.fact?.advanced?.fold_group === group,
        ))
          current[sibling.leafId] = { amount: target, mode: "open" };
      } else {
        if (group)
          for (const sibling of module.leaves.filter(
            (candidate) => candidate.fact?.bay_id === leaf.fact!.bay_id,
          ))
            current[sibling.leafId] = { amount: 0, mode: "open" };
        current[leaf.leafId] = { amount: target, mode: pose };
      }
      return { ...previous, [module.moduleId]: current };
    });
  };
  const download = () => {
    if (!capture.current) return;
    try {
      const link = document.createElement("a");
      link.href = capture.current();
      link.download = `ventana-${preset === "exterior" ? "exterior" : preset === "detail" ? "detalle" : "interior"}.png`;
      link.click();
    } catch {
      setError(true);
    }
  };
  if (!product.assembly.modules.length)
    return (
      <div className="model3d-fallback">
        <p>
          Sin vano definido.{" "}
          {audience === "portal"
            ? "Solicite el dibujo al fabricante."
            : "Agrega una posición para ver su geometría."}
        </p>
      </div>
    );
  if (!webglAvailable())
    return (
      <div className="model3d-fallback">
        <p>
          Este equipo no tiene aceleración gráfica para el 3D.{" "}
          {audience === "portal" ? "Use" : "Usa"} el dibujo técnico de esta posición.
        </p>
      </div>
    );
  if (error)
    return (
      <div className="model3d-fallback" role="alert">
        <p>
          No se pudo dibujar el 3D: se perdió el contexto gráfico.{" "}
          {audience === "portal" ? "Reintente o use" : "Reintenta o usa"} el dibujo técnico.
        </p>
        <button
          type="button"
          onClick={() => {
            setError(false);
            setExportReady(false);
            setAttempt((value) => value + 1);
          }}
        >
          Reintentar 3D
        </button>
      </div>
    );
  return (
    <div className="model3d-view" data-view={preset}>
      <div className="model3d-toolbar" role="toolbar" aria-label="Cámara y presentación 3D">
        <div className="ui-segmented model3d-segmented" role="group" aria-label="Cámara">
          {(
            [
              ["interior", "Interior"],
              ["exterior", "Exterior"],
              ["detail", "Detalle"],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              type="button"
              aria-pressed={preset === value}
              className={preset === value ? "is-active" : ""}
              onClick={() => setPreset(value)}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="ui-segmented model3d-segmented" role="group" aria-label="Lectura">
          <button
            type="button"
            aria-pressed={mode === "commercial"}
            onClick={() => setMode("commercial")}
          >
            Comercial
          </button>
          <button
            type="button"
            aria-pressed={mode === "technical"}
            onClick={() => setMode("technical")}
          >
            Técnica
          </button>
        </div>
        <button
          type="button"
          className="model3d-icon-button model3d-download"
          aria-label="Descargar imagen"
          title="Descargar imagen"
          disabled={!exportReady}
          onClick={download}
        >
          <Icon name="download" size={16} />
        </button>
      </div>
      <div className="model3d-toolbar model3d-toolbar--toggles" role="toolbar" aria-label="Capas">
        <button
          type="button"
          className="model3d-toggle-chip"
          aria-pressed={wall}
          onClick={() => setWall((value) => !value)}
        >
          Muro
        </button>
        <button
          type="button"
          className="model3d-toggle-chip"
          aria-pressed={clip}
          onClick={() => setClip((value) => !value)}
        >
          Corte
        </button>
        <button
          type="button"
          className="model3d-toggle-chip"
          aria-pressed={explode}
          onClick={() => {
            setStates({});
            setExplode((value) => !value);
          }}
        >
          Despiece
        </button>
        {hasLeaves && (
          <details className="model3d-leaves">
            <summary>Hojas</summary>
            <div className="model3d-leaf-list">
              {scene.modules.flatMap((module, moduleIndex) =>
                module.leaves.map((leaf) => {
                  const state = states[module.moduleId]?.[leaf.leafId];
                  const tilted =
                    leaf.kind === "tilt_turn" || leaf.fact?.opening.movement === "PARALLEL_SLIDE";
                  return (
                    <div className="model3d-leaf-row" key={`${module.moduleId}/${leaf.leafId}`}>
                      <span>
                        {scene.modules.length > 1 ? `Vano ${moduleIndex + 1} · ` : ""}
                        {leaf.label ?? "Hoja"}
                      </span>
                      <button
                        type="button"
                        aria-pressed={Boolean(state?.amount && state.mode === "open")}
                        onClick={() => changeLeaf(module, leaf, "open")}
                      >
                        {state?.amount && state.mode === "open" ? "Cerrar" : "Abrir"}
                      </button>
                      {tilted && (
                        <button
                          type="button"
                          aria-pressed={Boolean(state?.amount && state.mode === "tilt")}
                          onClick={() => changeLeaf(module, leaf, "tilt")}
                        >
                          Abatir
                        </button>
                      )}
                      {leaf.fact?.advanced?.pass_through && (
                        <button
                          type="button"
                          aria-pressed={Boolean(state?.amount && state.mode === "pass")}
                          onClick={() => changeLeaf(module, leaf, "pass")}
                        >
                          Hoja de paso
                        </button>
                      )}
                    </div>
                  );
                }),
              )}
            </div>
          </details>
        )}
        <span className="model3d-face sr-only" aria-live="polite">
          Vista{" "}
          {preset === "exterior" ? "exterior" : preset === "detail" ? "de detalle" : "interior"}
        </span>
      </div>
      {(approximate || approximateColor || schematicHardware || wall || explode) && (
        <p className="model3d-illustrative" role="note">
          {[
            approximate ? "Sección aproximada" : null,
            approximateColor ? "Color plano aproximado" : null,
            schematicHardware ? "Herrajes esquemáticos · altura del modelo" : null,
            wall ? "Muro de referencia" : null,
            explode ? "Despiece axial · marco, hojas, junquillos y vidrio" : null,
          ]
            .filter(Boolean)
            .join(" · ")}
        </p>
      )}
      {scene.diagnostics.length > 0 && (
        <div className="model3d-diagnostics" role="status">
          {scene.diagnostics.map((item, index) => (
            <span className="model3d-diag" key={index}>
              {item.code === "opening_authority_missing"
                ? String(item.values.what)
                : item.code === "kit_unknown"
                  ? "Sin dato de herraje: revise el kit en Catálogo"
                  : item.code === "handle_out_of_range"
                    ? "Manilla fuera de rango: revise la altura"
                    : item.code === "handle_datum_unsupported"
                      ? "Manilla de referencia, sin modelo del proveedor"
                      : "Herrajes aproximados"}
            </span>
          ))}
        </div>
      )}
      <RenderBoundary key={attempt} onError={onError}>
        <Canvas
          frameloop="demand"
          dpr={[1, 1.5]}
          gl={{ antialias: true, preserveDrawingBuffer: true, toneMapping: STUDIO_TONE_MAPPING }}
          camera={{ position: [0, 0, scene.radius * 4], fov: 42, near: 1, far: scene.radius * 30 }}
          className="model3d-canvas"
        >
          <Model3DStage
            scene={scene}
            states={states}
            selection={selection}
            theme="light"
            mode={mode}
            preset={preset}
            clip={clip}
            explode={explode}
            wall={wall}
            onPick={pick}
            onExport={onExport}
            onError={onError}
          />
        </Canvas>
      </RenderBoundary>
    </div>
  );
}
