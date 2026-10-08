import { useEffect, useState, type PropsWithChildren } from "react";
import { Link } from "react-router-dom";
import { Wordmark } from "../brand/Brand";
import { EmptyIllustration } from "../ui/EmptyIllustration";
import "./recovery.css";

export type RecoveryKind = "not-found" | "error" | "offline";

const COPY = {
  "not-found": [
    "Esta dirección no existe",
    "El enlace puede estar incompleto o haber cambiado. Vuelve al inicio para abrir la obra o la orden.",
  ],
  error: [
    "No se pudo abrir esta pantalla",
    "La pantalla dejó de responder. Recarga para recuperar los datos guardados.",
  ],
  offline: [
    "Sin conexión",
    "El navegador perdió la conexión. Conservamos esta pantalla; vuelve a conectarte y comprueba el acceso.",
  ],
} as const;

export function RecoveryPage({
  kind,
  technical,
  onRetry,
  retrying,
  notice,
}: {
  kind: RecoveryKind;
  technical?: string;
  onRetry?: () => void;
  retrying?: boolean;
  notice?: string;
}): JSX.Element {
  return (
    <main className="recovery-page" data-density="office">
      <section
        className="recovery-sheet"
        aria-labelledby="recovery-title"
        role={kind === "error" ? "alert" : undefined}
      >
        <Wordmark width={144} />
        <EmptyIllustration kind={kind === "offline" ? "connection" : "sheet"} />
        <h1 id="recovery-title">{COPY[kind][0]}</h1>
        <p>{COPY[kind][1]}</p>
        {notice ? <p role="status">{notice}</p> : null}
        {technical ? (
          <details>
            <summary>Detalles técnicos</summary>
            <p>{technical}</p>
          </details>
        ) : null}
        {kind === "not-found" ? (
          <Link className="ui-button ui-button--primary" to="/">
            Volver al inicio
          </Link>
        ) : (
          <button
            className="ui-button ui-button--primary"
            type="button"
            disabled={retrying}
            onClick={onRetry ?? (() => window.location.reload())}
          >
            {retrying
              ? "Comprobando conexión"
              : kind === "offline"
                ? "Comprobar conexión"
                : "Recargar pantalla"}
          </button>
        )}
      </section>
    </main>
  );
}

/** Keep route children mounted: going offline cannot discard an editor draft. */
export function ConnectionBoundary({ children }: PropsWithChildren): JSX.Element {
  const [online, setOnline] = useState(() => navigator.onLine);
  const [checking, setChecking] = useState(false);
  const [notice, setNotice] = useState<string>();
  async function probe(): Promise<void> {
    setChecking(true);
    setNotice(undefined);
    try {
      const response = await fetch(`/?connection-probe=${Date.now()}`, {
        method: "HEAD",
        cache: "no-store",
        signal: AbortSignal.timeout(5000),
      });
      if (!response.ok) throw new Error("unreachable");
      setOnline(true);
    } catch {
      setNotice(
        "El servidor sigue sin responder. Conservamos tu pantalla y sus cambios pendientes.",
      );
    } finally {
      setChecking(false);
    }
  }
  useEffect(() => {
    const sync = () => setOnline(navigator.onLine);
    window.addEventListener("online", sync);
    window.addEventListener("offline", sync);
    return () => {
      window.removeEventListener("online", sync);
      window.removeEventListener("offline", sync);
    };
  }, []);
  return (
    <>
      <div className="connection-content" hidden={!online}>
        {children}
      </div>
      {!online ? (
        <RecoveryPage
          kind="offline"
          retrying={checking}
          notice={notice}
          onRetry={() => {
            void probe();
          }}
        />
      ) : null}
    </>
  );
}
