declare module "react" {
  export interface ReactElement {
    readonly type: unknown;
    readonly props: Readonly<Record<string, unknown>>;
    readonly key: string | null;
  }

  export const StrictMode: unique symbol;

  export function createElement(
    type: unknown,
    props: Readonly<Record<string, unknown>> | null,
    ...children: readonly ReactElement[]
  ): ReactElement;
}

declare module "react-dom/client" {
  import type { ReactElement } from "react";

  interface Root {
    render(element: ReactElement): void;
  }

  export function createRoot(container: Element | DocumentFragment): Root;
}
