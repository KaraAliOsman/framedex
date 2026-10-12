import { useEffect, useState } from "react";
import { analyticsPreferences, analyticsPreferencesSave } from "../../api/generated/dekopen";
import { Button, ErrorState, LoadingState, Qty, ValidatedForm } from "../../ui";
import { actionErrorDetail } from "../errors";

export function AnalyticsPreferences({
  orgId,
  canEdit,
}: {
  orgId: string;
  canEdit: boolean;
}): JSX.Element {
  const [days, setDays] = useState<number>();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let live = true;
    setDays(undefined);
    setError("");
    void analyticsPreferences()
      .then((r) => {
        if (!("period_days" in r.data)) throw new Error("analytics_preferences");
        if (live) setDays(r.data.period_days);
      })
      .catch((e) => {
        if (live) setError(actionErrorDetail(e, "No pudimos leer el período de analítica."));
      });
    return () => {
      live = false;
    };
  }, [orgId, attempt]);
  return (
    <section className="settings-card">
      <h2>Período de Analítica</h2>
      <p>
        La cohorte inicial cubre los últimos días hasta hoy, en la zona horaria de tu organización.
        Puedes elegir otras fechas en Analítica.
      </p>
      {days === undefined && !error ? (
        <LoadingState label="Leyendo el período de analítica" />
      ) : typeof days === "number" ? (
        <ValidatedForm
          onSubmit={(e) => {
            e.preventDefault();
            setBusy(true);
            setSaved(false);
            setError("");
            void analyticsPreferencesSave({ period_days: days })
              .then(() => setSaved(true))
              .catch((e) => setError(actionErrorDetail(e, "No pudimos guardar el período.")))
              .finally(() => setBusy(false));
          }}
        >
          <label>
            Días del período inicial
            <input
              type="number"
              min={1}
              max={366}
              step={1}
              required
              value={days}
              disabled={!canEdit}
              onChange={(e) => setDays(Number(e.target.value))}
            />
          </label>
          {canEdit && (
            <Button type="submit" variant="primary" loading={busy}>
              Guardar período
            </Button>
          )}
          {saved && (
            <p role="status">
              Período inicial guardado: <Qty value={String(days)} unit="días" />.
            </p>
          )}
        </ValidatedForm>
      ) : null}
      {!canEdit && <p>El dueño puede cambiar el período inicial de la organización.</p>}
      {error && (
        <ErrorState
          body={error}
          onRetry={days === undefined ? () => setAttempt((value) => value + 1) : undefined}
        />
      )}
    </section>
  );
}
