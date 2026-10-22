import { App } from "./App";
import { AuthSessionProvider } from "./auth/AuthSessionProvider";
import { CatalogChangeReviewProvider } from "./features/catalogs/CatalogChangeReview";

export default function PrivateApplication(): JSX.Element {
  return (
    <AuthSessionProvider>
      <CatalogChangeReviewProvider>
        <App />
      </CatalogChangeReviewProvider>
    </AuthSessionProvider>
  );
}
