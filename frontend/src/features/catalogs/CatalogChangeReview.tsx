import { type PropsWithChildren, useEffect, useRef, useState } from "react";

import { configureCatalogChangeReview } from "../../api/apiMutator";
import type { ReferenceChangeReview } from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { fmtMm } from "../../format";
import { domainLabel } from "../../i18n/domainLabels";
import { Button, Dialog } from "../../ui";
import { ReferenceOutputChanges } from "./ReferenceOutputChanges";
import "./series-trial.css";

type Pending = { review: ReferenceChangeReview; resolve: (token: string | null) => void };

export function CatalogChangeReviewProvider({ children }: PropsWithChildren): JSX.Element {
  const { me, session } = useAuthSession();
  return (
    <ReviewQueue key={`${session?.user.id}:${me?.active_organization?.id}`}>{children}</ReviewQueue>
  );
}

function ReviewQueue({ children }: PropsWithChildren): JSX.Element {
  const queue = useRef<Pending[]>([]);
  const active = useRef<Pending | null>(null);
  const [pending, setPending] = useState<Pending | null>(null);
  useEffect(() => {
    const remove = configureCatalogChangeReview(async (payload) => {
      const review = payload as ReferenceChangeReview;
      if (!review || typeof review.review_token !== "string" || !Array.isArray(review.changes))
        return null;
      return new Promise<string | null>((resolve) => {
        const next = { review, resolve };
        if (active.current) queue.current.push(next);
        else {
          active.current = next;
          setPending(next);
        }
      });
    });
    return () => {
      remove();
      active.current?.resolve(null);
      queue.current.forEach((item) => item.resolve(null));
      active.current = null;
      queue.current = [];
    };
  }, []);
  function settle(accept: boolean) {
    const current = active.current;
    if (!current) return;
    current.resolve(accept ? current.review.review_token : null);
    active.current = queue.current.shift() ?? null;
    setPending(active.current);
  }
  return (
    <>
      {children}
      {pending && (
        <Dialog
          title="Esta edición cambia tu ventana de prueba"
          width="xl"
          onClose={() => settle(false)}
          footer={
            <>
              <Button onClick={() => settle(false)}>Conservar mi borrador</Button>
              <Button variant="primary" onClick={() => settle(true)}>
                Guardar cambio y volver a verificar
              </Button>
            </>
          }
        >
          <p>
            Compara el despiece antes de guardar. La prueba original se conserva y tendrás que
            verificar la serie de nuevo.
          </p>
          {pending.review.changes.map((change, index) => {
            const before = new Map(change.before.measurements.map((row) => [row.key, row]));
            const after = new Map(change.after.measurements.map((row) => [row.key, row]));
            return (
              <section key={`${change.reference_id}:${index}`} className="series-trial">
                <h3>Ventana de prueba {index + 1}</h3>
                {change.before.error && <p role="alert">Antes: {change.before.error}</p>}
                {change.after.error && <p role="alert">Después: {change.after.error}</p>}
                <div
                  className="series-trial__scroll"
                  role="region"
                  aria-label={`Cambios de la prueba ${index + 1}`}
                  tabIndex={0}
                >
                  <table className="series-trial__table">
                    <thead>
                      <tr>
                        <th>Pieza</th>
                        <th>Antes · mm</th>
                        <th>Después · mm</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...new Set([...before.keys(), ...after.keys()])].map((key) => {
                        const a = before.get(key),
                          b = after.get(key),
                          row = b ?? a!;
                        return (
                          <tr
                            key={key}
                            data-changed={
                              a?.value_mm !== b?.value_mm ||
                              a?.quantity !== b?.quantity ||
                              a?.sku !== b?.sku ||
                              a?.angle_left !== b?.angle_left ||
                              a?.angle_right !== b?.angle_right
                            }
                          >
                            <th scope="row">
                              {domainLabel(row.role)} · {row.sku}
                              <small>
                                {row.field === "width_mm"
                                  ? "Ancho"
                                  : row.field === "height_mm"
                                    ? "Alto"
                                    : "Largo"}
                              </small>
                            </th>
                            <td>
                              {a ? (
                                <>
                                  {a.quantity} × {fmtMm(a.value_mm)}
                                  <small>
                                    {a.angle_left !== null && a.angle_right !== null
                                      ? `${fmtMm(a.angle_left)}° / ${fmtMm(a.angle_right)}°`
                                      : "No aplica"}
                                  </small>
                                </>
                              ) : (
                                "Sin pieza"
                              )}
                            </td>
                            <td>
                              {b ? (
                                <>
                                  {b.quantity} × {fmtMm(b.value_mm)}
                                  <small>
                                    {b.angle_left !== null && b.angle_right !== null
                                      ? `${fmtMm(b.angle_left)}° / ${fmtMm(b.angle_right)}°`
                                      : "No aplica"}
                                  </small>
                                </>
                              ) : (
                                "Sin pieza"
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <ReferenceOutputChanges before={change.before.output} after={change.after.output} />
              </section>
            );
          })}
        </Dialog>
      )}
    </>
  );
}
