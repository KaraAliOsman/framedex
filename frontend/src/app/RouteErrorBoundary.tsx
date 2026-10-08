import { Component, type ErrorInfo, type ReactNode } from "react";
import { RecoveryPage } from "./RecoveryPage";

type Props = { children: ReactNode };
type State = { error: Error | null };

/** Catches a render crash in any route and keeps the app recoverable —
 * without it a single bad component takes the whole SPA down to a blank
 * page. Chunk-load failures (a new deploy mid-session) land here too and get
 * the same "recargar" recovery path. */
export class RouteErrorBoundary extends Component<Props, State> {
  override state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    // eslint-disable-next-line no-console
    console.error("route_error", error, info.componentStack);
  }

  override render(): ReactNode {
    if (!this.state.error) return this.props.children;
    return <RecoveryPage kind="error" technical={this.state.error.name} />;
  }
}
