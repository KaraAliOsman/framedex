import { useState } from "react";
import { Link } from "react-router-dom";
import { CompanyCard } from "../settings/AdminSections";
import { DocumentSettings } from "../projects/DocumentSettings";
import { PricingRulesSettings } from "../pricing/PricingPage";
import { Button, Stepper } from "../../ui";

export function CompanySetup({
  orgId,
  owner,
  onComplete,
}: {
  orgId: string;
  owner: boolean;
  onComplete: () => void;
}): JSX.Element {
  const [step, setStep] = useState(0),
    [saved, setSaved] = useState(false);
  const names = ["Empresa", "Comercial", "Documentos"];
  return (
    <section className="onboarding" data-density="office">
      <header className="onboarding-head">
        <p className="ui-spec-label">Configuración inicial</p>
        <h1>Prepara tu empresa</h1>
        <p>
          Confirma identidad, condiciones y papel antes de tu primera obra. Los valores sugeridos
          son editables y se guardan para las nuevas emisiones.
        </p>
      </header>
      <Stepper
        current={String(step)}
        steps={names.map((label, index) => ({
          id: String(index),
          label,
          onSelect: () => {
            setStep(index);
            setSaved(false);
          },
          disabledReason: index > step ? "Guarda y confirma el paso actual." : undefined,
        }))}
      />
      <div className="onboarding-card">
        {step === 0 ? (
          <>
            <CompanyCard orgId={orgId} canEdit={owner} onSaved={() => setSaved(true)} />
            {!owner && (
              <>
                <p>
                  El dueño confirma la identidad legal y la moneda. Puedes preparar las condiciones
                  comerciales que permite tu rol.
                </p>
                <Button onClick={() => setSaved(true)}>Continuar con mi acceso</Button>
              </>
            )}
          </>
        ) : (
          <>
            <DocumentSettings
              key={step}
              orgId={orgId}
              canEdit
              section={step === 1 ? "commercial" : "documents"}
              onSaved={() => setSaved(true)}
            />
            {step === 1 && owner && (
              <>
                <p>IVA y banda de margen se configuran con la autoridad comercial existente.</p>
                <PricingRulesSettings orgId={orgId} />
              </>
            )}
          </>
        )}
        <div className="onboarding-actions">
          <Button
            disabled={!saved}
            variant="primary"
            onClick={() => {
              if (step === 2) onComplete();
              else {
                setStep(step + 1);
                setSaved(false);
              }
            }}
          >
            {step === 2 ? "Crear primer proyecto" : "Confirmar y continuar"}
          </Button>
          <Link to="/settings/general?section=company">Abrir ajustes completos</Link>
        </div>
      </div>
    </section>
  );
}
