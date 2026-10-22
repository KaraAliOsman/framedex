import { Link } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { CatalogImportsPanel } from "./CatalogImportsPanel";
import "./catalogs.css";

/** A source link needs its import, not every article and kit in the catalog. */
export function CatalogImportReviewPage({
  orgId,
  importId,
  canWrite,
}: {
  orgId: string;
  importId: string;
  canWrite: boolean;
}): JSX.Element {
  const client = useQueryClient();
  return (
    <section className="catalog catalog-import-page" aria-label="Revisar manual">
      <header>
        <Link to="/catalogs/systems">‹ Catálogo</Link>
        <h1>Revisar manual</h1>
        <p>Contrasta las propuestas con el original antes de publicarlas.</p>
      </header>
      <CatalogImportsPanel
        orgId={orgId}
        initialImportId={importId}
        reviewOnly
        canWrite={canWrite}
        systems={[]}
        onConfirmed={() => {
          void client.invalidateQueries({ queryKey: ["series-sheet", orgId] });
          void client.invalidateQueries({ queryKey: ["catalog-home", orgId] });
        }}
      />
    </section>
  );
}
