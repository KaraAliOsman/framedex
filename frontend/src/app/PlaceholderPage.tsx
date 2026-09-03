import { t } from "../i18n/es-CL";

type PlaceholderPageProps = {
  title: string;
  description: string;
};

export function PlaceholderPage({ title, description }: PlaceholderPageProps): JSX.Element {
  return (
    <section className="placeholder" aria-labelledby="page-title">
      <p className="eyebrow">{t("shell.placeholder")}</p>
      <h1 id="page-title">{title}</h1>
      <p>{description}</p>
    </section>
  );
}
