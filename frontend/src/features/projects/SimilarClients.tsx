import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { clientDirectory } from "../../api/generated/dekopen";

type Match = { id: string; name: string; rut: string };

/** Before creating a client: existing records with the same RUT or a similar
 * name, so the person reuses the record instead of duplicating it. */
export function SimilarClients({
  orgId,
  name,
  rut,
}: {
  orgId: string;
  name: string;
  rut: string;
}): JSX.Element | null {
  const [matches, setMatches] = useState<Match[]>([]);
  const term = (rut.trim().length >= 7 ? rut.trim() : name.trim()).slice(0, 255);
  useEffect(() => {
    if (term.length < 3) {
      setMatches([]);
      return;
    }
    let live = true;
    const timer = window.setTimeout(() => {
      void clientDirectory({ q: term, limit: 5 }, { headers: { "X-Organization-ID": orgId } })
        .then((response) => {
          if (!live || response.status !== 200) return;
          setMatches(
            response.data.items.map((item) => ({ id: item.id, name: item.name, rut: item.rut })),
          );
        })
        .catch(() => {
          if (live) setMatches([]);
        });
    }, 350);
    return () => {
      live = false;
      window.clearTimeout(timer);
    };
  }, [term, orgId]);
  if (!matches.length) return null;
  return (
    <div className="customer-similar" role="status">
      <p>Ya hay clientes parecidos. Abre la ficha existente para no duplicarla:</p>
      <ul>
        {matches.map((match) => (
          <li key={match.id}>
            <Link to={`/clients/${match.id}`}>
              {match.name}
              {match.rut ? ` · ${match.rut}` : ""}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
