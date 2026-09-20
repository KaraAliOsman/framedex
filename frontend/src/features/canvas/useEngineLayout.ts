import { useEffect, useState } from "react";
import { engineLayout } from "../../api/generated/dekopen";
import type { NodeLayout } from "../../api/generated/models";
import type { CanvasDesignInputs } from "./canvasStore";
import { requestFromInputs } from "./useEngineCalculation";

export function useEngineLayout(inputs: CanvasDesignInputs, organizationId: string): NodeLayout[] {
  const [resolved, setResolved] = useState<{
    inputs: CanvasDesignInputs;
    organizationId: string;
    nodes: NodeLayout[];
  }>();
  useEffect(() => {
    let active = true;
    if (inputs.systemId) {
      void engineLayout(requestFromInputs(inputs), {
        headers: { "X-Organization-ID": organizationId },
      })
        .then((response) => {
          if (active && response.status === 200)
            setResolved({ inputs, organizationId, nodes: response.data.nodes });
        })
        .catch(() => {
          /* Unresolved geometry remains schematic; shortcuts stay unavailable. */
        });
    }
    return () => {
      active = false;
    };
  }, [inputs, organizationId]);
  return resolved?.inputs === inputs && resolved.organizationId === organizationId
    ? resolved.nodes
    : [];
}
