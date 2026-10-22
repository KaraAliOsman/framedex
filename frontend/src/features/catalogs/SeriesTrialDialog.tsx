import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import type { SeriesSheet } from "../../api/generated/models";
import { Button, Dialog } from "../../ui";
import { SeriesTrial } from "./SeriesTrial";

export function SeriesTrialDialog({
  orgId,
  sheet,
  onClose,
  onComplete,
}: {
  orgId: string;
  sheet: SeriesSheet;
  onClose: () => void;
  onComplete: () => void;
}): JSX.Element {
  const client = useQueryClient();
  const [current, setCurrent] = useState(sheet);
  const [busy, setBusy] = useState(false);
  function saved(next: SeriesSheet) {
    setCurrent(next);
    client.setQueryData(["series-sheet", orgId, sheet.id], next);
    void client.invalidateQueries({ queryKey: ["catalog-home", orgId] });
  }
  return (
    <Dialog
      title="Ventana de prueba"
      width="xl"
      onClose={() => {
        if (!busy) onClose();
      }}
    >
      <SeriesTrial
        orgId={orgId}
        sheet={current}
        onSaved={saved}
        onBusyChange={setBusy}
        onComplete={onComplete}
      />
      <Button disabled={busy} onClick={onClose}>
        Volver a la serie
      </Button>
    </Dialog>
  );
}
