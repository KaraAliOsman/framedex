import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { invitationInspect, invitationAccept } from "../api/generated/dekopen";
import type { InvitationInspect } from "../api/generated/models";
import { Button, ErrorState, LoadingState, useConfirm } from "../ui";
import { Wordmark } from "../brand/Brand";
import { roleNames } from "../features/settings/AdminSections";
import { actionErrorDetail } from "../features/errors";
import { useAuthSession } from "./AuthSessionProvider";

export const INVITATION_KEY = "dekopen.pending-invitation";

export function InvitationPage(): JSX.Element {
  const auth = useAuthSession(),
    navigate = useNavigate(),
    confirm = useConfirm(),
    [params, setParams] = useSearchParams();
  const [token] = useState(
    () => params.get("token") ?? sessionStorage.getItem(INVITATION_KEY) ?? "",
  );
  const [data, setData] = useState<InvitationInspect | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    if (token) {
      sessionStorage.setItem(INVITATION_KEY, token);
      setParams({}, { replace: true });
    }
  }, [token, setParams]);
  useEffect(() => {
    if (!auth.session || !token) return;
    let current = true;
    setBusy(true);
    void invitationInspect({ token })
      .then((result) => {
        if (current && result.status === 200) setData(result.data);
      })
      .catch((error) => {
        if (current)
          setError(actionErrorDetail(error, "El enlace no está disponible para este correo."));
      })
      .finally(() => {
        if (current) setBusy(false);
      });
    return () => {
      current = false;
    };
  }, [auth.session, token]);
  return (
    <main className="auth-screen">
      <section className="auth-card">
        <Wordmark width={176} />
        <h1>Invitación a una empresa</h1>
        {!token ? (
          <ErrorState body="Falta el enlace de invitación. Abre el correo enviado por el dueño." />
        ) : auth.session === null ? (
          <>
            <p>
              Entra con el correo que recibió la invitación. La membresía se crea cuando revisas y
              aceptas el rol.
            </p>
            <Link
              className="ui-button ui-button--primary"
              to="/login"
              state={{ from: "/invitation" }}
            >
              Entrar con mi correo
            </Link>
          </>
        ) : busy && data === null ? (
          <LoadingState label="Comprobando invitación" />
        ) : data ? (
          <>
            <p>{data.organization_name}</p>
            <p>
              {data.email} · {roleNames[data.role]}
            </p>
            {data.accepted ? (
              <>
                <p>Ya aceptaste esta invitación.</p>
                <Link className="ui-button" to="/">
                  Ir a mi empresa
                </Link>
              </>
            ) : (
              <Button
                variant="primary"
                disabled={busy}
                onClick={() =>
                  void (async () => {
                    if (
                      !(await confirm({
                        title: "Aceptar invitación",
                        body: `Entrarás en ${data.organization_name} como ${roleNames[data.role]}.`,
                      }))
                    )
                      return;
                    setBusy(true);
                    setError("");
                    try {
                      const result = await invitationAccept({ token });
                      if (result.status === 200) {
                        sessionStorage.removeItem(INVITATION_KEY);
                        await auth.selectOrganization(result.data.organization_id);
                        await auth.refreshContext();
                        navigate("/");
                      }
                    } catch (error) {
                      setError(
                        actionErrorDetail(
                          error,
                          "No se pudo aceptar. Si la empresa exige segundo factor, configúralo antes de reintentar.",
                        ),
                      );
                    } finally {
                      setBusy(false);
                    }
                  })()
                }
              >
                Aceptar invitación
              </Button>
            )}
            <Link className="ui-button" to="/auth/mfa?configure=1">
              Configurar segundo factor
            </Link>
          </>
        ) : null}
        {error && <p role="alert">{error}</p>}
      </section>
    </main>
  );
}
