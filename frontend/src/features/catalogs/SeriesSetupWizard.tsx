import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { ApiError } from "../../api/apiMutator";
import {
  catalogSeriesSetupProgress,
  catalogSeriesSaveSetupProgress,
  catalogSeriesSheet,
} from "../../api/generated/dekopen";
import type { SeriesSheet, SetupProgress, SetupStateRequest } from "../../api/generated/models";
import { UnsavedChangesGuard } from "../../app/UnsavedChangesGuard";
import { Button, Dialog, Loading, useConfirm } from "../../ui";
import { CatalogImportsPanel } from "./CatalogImportsPanel";
import { SupplierPriceImport } from "./SupplierPriceImport";
import { SeriesTrial } from "./SeriesTrial";
import { usageLabel } from "./seriesSheetModel";
import "./series-setup.css";
import "./catalogs.css";

const steps = ["Serie", "Manual", "Precios", "Ventana de prueba", "Primera cotización"];

export function SeriesSetupWizard({
  orgId,
  systemId,
  isOwner,
  onClose,
}: {
  orgId: string;
  systemId: string;
  isOwner: boolean;
  onClose: () => void;
}): JSX.Element {
  const query = useQuery({
    queryKey: ["series-setup", orgId, systemId],
    refetchOnWindowFocus: false,
    staleTime: 0,
    queryFn: async ({ signal }) => {
      const options = { headers: { "X-Organization-ID": orgId }, signal };
      const [sheet, progress] = await Promise.all([
        catalogSeriesSheet(systemId, options),
        catalogSeriesSetupProgress(systemId, options),
      ]);
      if (sheet.status !== 200 || progress.status !== 200) throw new Error("setup");
      return { sheet: sheet.data, progress: progress.data };
    },
  });
  if (!query.data || query.isFetching)
    return (
      <Dialog title="Preparar mi serie" width="xl" onClose={onClose}>
        {query.isError ? (
          <>
            <p role="alert">No se pudo recuperar el alta.</p>
            <Button onClick={() => void query.refetch()}>Volver a intentar</Button>
          </>
        ) : (
          <Loading label="Recuperando el alta de la serie" />
        )}
      </Dialog>
    );
  if (query.data.sheet.tabs.rules.read_only || query.data.sheet.usage.is_example)
    return (
      <Dialog title="Preparar mi serie" onClose={onClose}>
        <p>
          Prepara una serie de tu taller. Los ejemplos y la biblioteca se consultan desde su ficha.
        </p>
      </Dialog>
    );
  return <SetupSteps orgId={orgId} isOwner={isOwner} initial={query.data} onClose={onClose} />;
}

function SetupSteps({
  orgId,
  isOwner,
  initial,
  onClose,
}: {
  orgId: string;
  isOwner: boolean;
  initial: { sheet: SeriesSheet; progress: SetupProgress };
  onClose: () => void;
}): JSX.Element {
  const client = useQueryClient();
  const navigate = useNavigate();
  const confirm = useConfirm();
  const [sheet, setSheet] = useState(initial.sheet);
  const [progress, setProgress] = useState(initial.progress);
  const current = useRef(initial.progress);
  const queue = useRef(Promise.resolve());
  const failed = useRef(false);
  const [pending, setPending] = useState(0);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");
  const [moduleBusy, setModuleBusy] = useState(false);
  const [manualDirty, setManualDirty] = useState(false);
  const [pricesDirty, setPricesDirty] = useState(false);
  const [trialDirty, setTrialDirty] = useState(false);
  const [visited, setVisited] = useState(() => new Set([initial.progress.step]));
  const [generation, setGeneration] = useState(0);
  const surface = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const body = surface.current?.parentElement;
    if (body) body.scrollTop = 0;
  }, [progress.step]);
  const busy = pending > 0 || syncing || moduleBusy;
  const dirty = manualDirty || pricesDirty || trialDirty;
  const system = sheet.tabs.rules;
  const options = { headers: { "X-Organization-ID": orgId } };
  function accept(next: SeriesSheet) {
    setSheet(next);
    client.setQueryData(["series-sheet", orgId, system.id], next);
    void client.invalidateQueries({ queryKey: ["catalog-home", orgId] });
  }
  // Each write uses the revision returned by its predecessor. A failed write
  // stops the queue; recovering another screen's state is an explicit action.
  function save(step: number, patch: SetupStateRequest = {}) {
    setPending((count) => count + 1);
    queue.current = queue.current
      .then(async () => {
        if (failed.current) return;
        try {
          const response = await catalogSeriesSaveSetupProgress(
            system.id,
            {
              step,
              revision: current.current.revision,
              state: { ...current.current.state, ...patch },
            },
            options,
          );
          if (response.status !== 200) throw new ApiError(response.status, response.data);
          current.current = response.data;
          setProgress(response.data);
          setVisited((value) => new Set([...value, step]));
        } catch (failure) {
          failed.current = true;
          setError(
            failure instanceof ApiError && failure.status === 409
              ? "El alta cambió en otra pantalla. Recupera su progreso antes de continuar."
              : "No se pudo guardar el progreso. Conservamos los borradores abiertos. Recupera el alta para volver a intentar.",
          );
        }
      })
      .finally(() => setPending((count) => count - 1));
  }
  async function refresh(verified = false) {
    if (
      !verified &&
      dirty &&
      !(await confirm({
        title: "¿Recuperar el alta guardada?",
        body: "Los borradores abiertos sin publicar se descartarán. El catálogo y los precios guardados se conservan.",
      }))
    )
      return;
    setSyncing(true);
    await queue.current;
    try {
      const [nextSheet, nextProgress] = await Promise.all([
        catalogSeriesSheet(system.id, options),
        catalogSeriesSetupProgress(system.id, options),
      ]);
      if (nextSheet.status !== 200 || nextProgress.status !== 200) throw new Error("reload");
      accept(nextSheet.data);
      current.current = nextProgress.data;
      setProgress(nextProgress.data);
      if (verified) {
        setVisited((value) => new Set([...value, nextProgress.data.step]));
      } else {
        setVisited(new Set([nextProgress.data.step]));
        setGeneration((value) => value + 1);
        setManualDirty(false);
        setPricesDirty(false);
        setTrialDirty(false);
      }
      failed.current = false;
      setError("");
    } catch {
      setError(
        "No se pudo recuperar el alta. Tus borradores siguen abiertos; vuelve a intentarlo.",
      );
    } finally {
      setSyncing(false);
    }
  }
  async function close() {
    if (busy) return;
    if (
      (dirty || failed.current) &&
      !(await confirm({
        title: "¿Cerrar el alta por ahora?",
        body: "El progreso guardado se conserva. Los archivos seleccionados y las revisiones sin publicar se descartarán.",
      }))
    )
      return;
    onClose();
  }
  async function refreshSheet() {
    const response = await catalogSeriesSheet(system.id, options);
    if (response.status === 200) accept(response.data);
    else throw new Error("sheet");
  }
  const step = progress.step;
  const quote = sheet.usage.levels.find((item) => item.level === "QUOTABLE");
  const quotable = quote?.ok === true;
  return (
    <Dialog title="Preparar mi serie" width="xl" onClose={() => void close()}>
      <UnsavedChangesGuard
        dirty={dirty || busy || !!error}
        message="Hay borradores del alta sin guardar o publicar."
      />
      <div className="series-setup" ref={surface}>
        <header className="series-setup__identity">
          <strong>{system.name}</strong>
          <span>
            {system.manufacturer || "Tu taller"} · {system.code}
          </span>
        </header>
        <nav aria-label="Pasos del alta">
          <ol className="series-setup__steps">
            {steps.map((label, index) => (
              <li key={label}>
                <button
                  type="button"
                  aria-label={`Paso ${index + 1}: ${label}`}
                  disabled={busy || !!error}
                  aria-current={step === index + 1 ? "step" : undefined}
                  onClick={() => save(index + 1)}
                >
                  <span aria-hidden="true">{index + 1}</span>
                  {label}
                </button>
              </li>
            ))}
          </ol>
        </nav>
        <p className="series-setup__saved" role="status">
          {pending ? "Guardando progreso…" : "Progreso guardado · Puedes continuar después."}
        </p>
        {error && (
          <div>
            <p role="alert">{error}</p>
            <Button disabled={busy} onClick={() => void refresh()}>
              Recuperar alta guardada
            </Button>
          </div>
        )}
        <fieldset
          className="series-setup__body"
          disabled={pending > 0 || syncing || !!error}
          key={generation}
        >
          {visited.has(1) && (
            <section hidden={step !== 1} aria-label="Serie del alta">
              <h2>Tu serie, paso a paso</h2>
              <p>
                La plantilla aporta valores sugeridos. Agrega los perfiles del manual, tus precios y
                comprueba una ventana antes de fabricar.
              </p>
              <dl>
                <dt>Serie</dt>
                <dd>{system.name}</dd>
                <dt>Código</dt>
                <dd>{system.code}</dd>
                <dt>Preparación actual</dt>
                <dd>{usageLabel(sheet.usage)}</dd>
              </dl>
              <p>
                Si necesitas completar perfiles, aperturas o vidrios, guarda este paso y vuelve a la
                ficha. Puedes continuar el alta desde allí.
              </p>
            </section>
          )}
          {visited.has(2) && (
            <section className="catalog" hidden={step !== 2} aria-label="Manual del alta">
              <h2>Agrega el manual de tu serie</h2>
              <p>
                Revisa las propuestas y publica solo los cambios que contrastaste. Puedes seguir si
                ya completaste la ficha.
              </p>
              <CatalogImportsPanel
                orgId={orgId}
                canWrite
                systems={[system]}
                initialImportId={progress.state.manual_import_id ?? undefined}
                onConfirmed={() =>
                  void refreshSheet().catch(() =>
                    setError(
                      "Los cambios se publicaron. Recupera el alta para actualizar la ficha.",
                    ),
                  )
                }
                setup={{
                  systemCode: system.code,
                  onImport: (id) => save(current.current.step, { manual_import_id: id }),
                  onBusyChange: setModuleBusy,
                  onDirtyChange: setManualDirty,
                }}
              />
            </section>
          )}
          {visited.has(3) && (
            <section hidden={step !== 3} aria-label="Precios del alta">
              {isOwner ? (
                <>
                  <h2>Carga tus precios de compra</h2>
                  <p>
                    Los precios se revisan y guardan con un clic. Al reabrir conservamos el nombre
                    del último archivo guardado; los archivos sin guardar se eligen de nuevo.
                  </p>
                  {progress.state.prices_file_name && (
                    <p>Último archivo guardado: {progress.state.prices_file_name}</p>
                  )}
                  <SupplierPriceImport
                    orgId={orgId}
                    initialSupplier={system.manufacturer ?? ""}
                    onBusyChange={setModuleBusy}
                    onDirtyChange={setPricesDirty}
                    onApplied={(receipt) => {
                      save(current.current.step, { prices_file_name: receipt.fileName });
                      void refreshSheet().catch(() =>
                        setError(
                          "Los precios se guardaron. Recupera el alta para actualizar la ficha.",
                        ),
                      );
                    }}
                  />
                </>
              ) : (
                <>
                  <h2>Precios de compra</h2>
                  <p>
                    El dueño del taller puede cargar la lista. Puedes continuar con la ventana de
                    prueba; el último paso mostrará lo que falta para cotizar.
                  </p>
                </>
              )}
            </section>
          )}
          {visited.has(4) && (
            <section hidden={step !== 4} aria-label="Ventana del alta">
              <SeriesTrial
                orgId={orgId}
                sheet={sheet}
                initial={progress.state.trial}
                onSaved={accept}
                onDraft={(trial) => save(current.current.step, { trial })}
                onBusyChange={setModuleBusy}
                onDirtyChange={setTrialDirty}
                onVerified={() => void refresh(true)}
                onComplete={() => void close()}
              />
            </section>
          )}
          {visited.has(5) && (
            <section hidden={step !== 5} aria-label="Primera cotización">
              <h2>Prepara tu primera cotización</h2>
              <p>
                {usageLabel(sheet.usage)}.{" "}
                {sheet.usage.verified
                  ? "La ventana de prueba está guardada y protege los cambios de reglas."
                  : "Verifica la ventana de prueba antes de fabricar."}
              </p>
              {!quotable && (
                <>
                  <p>Completa estos datos para cotizar con esta serie:</p>
                  <div
                    className="series-setup__pending"
                    role="region"
                    aria-label="Datos pendientes para cotizar"
                    tabIndex={0}
                  >
                    <ul>
                      {quote?.pending.map((item, index) => (
                        <li key={index}>{item.action}</li>
                      ))}
                    </ul>
                  </div>
                </>
              )}
              <p>
                La nueva obra usará esta serie como opción inicial para sus ventanas. Podrás
                cambiarla en la obra.
              </p>
              <Button
                variant="primary"
                disabled={!quotable || busy || dirty || !!error}
                onClick={() =>
                  navigate(`/projects?create=1&system=${encodeURIComponent(system.id)}`)
                }
              >
                Crear mi primera cotización
              </Button>
            </section>
          )}
        </fieldset>
        <footer className="series-setup__footer">
          <Button disabled={busy} onClick={() => void close()}>
            Volver a la ficha
          </Button>
          {step < 5 && (
            <Button variant="primary" disabled={busy || !!error} onClick={() => save(step + 1)}>
              Continuar a {steps[step]}
            </Button>
          )}
        </footer>
      </div>
    </Dialog>
  );
}
