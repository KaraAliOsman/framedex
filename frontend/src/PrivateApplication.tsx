import { App } from "./App";
import { AuthSessionProvider } from "./auth/AuthSessionProvider";

export default function PrivateApplication(): JSX.Element {
  return (
    <AuthSessionProvider>
      <App />
    </AuthSessionProvider>
  );
}
