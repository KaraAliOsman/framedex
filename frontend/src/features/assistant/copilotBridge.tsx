import { createContext, useContext, type ReactNode } from "react";

/** The one way manual surfaces may hand work to the optional copilot.
 *
 * Provided by the shell only when the organization has the AI core; in the
 * manual plan `available` is false and no surface shows an assistant
 * affordance (no dead buttons, no chips). Delegating opens the single global
 * popup with an explicit, sealed context — it never calls the model by itself
 * and never creates a private chat inside the canvas. */

export type CopilotDelegation = {
  mode: "chat" | "work";
  /** Prefilled composer text; the person still sends it. */
  text: string;
  /** Stable identity of what the request is about (never visual indexes). */
  refs?: Record<string, string | string[] | Record<string, unknown>>;
};

type CopilotBridge = {
  available: boolean;
  delegate(request: CopilotDelegation): void;
};

const CopilotContext = createContext<CopilotBridge>({
  available: false,
  delegate: () => undefined,
});

export const COPILOT_DELEGATE_EVENT = "dekopen:copilot-delegate";

export function CopilotProvider({
  available,
  children,
}: {
  available: boolean;
  children: ReactNode;
}): JSX.Element {
  return (
    <CopilotContext.Provider
      value={{
        available,
        delegate: (request) => {
          if (!available) return;
          window.dispatchEvent(new CustomEvent(COPILOT_DELEGATE_EVENT, { detail: request }));
        },
      }}
    >
      {children}
    </CopilotContext.Provider>
  );
}

export function useCopilot(): CopilotBridge {
  return useContext(CopilotContext);
}
