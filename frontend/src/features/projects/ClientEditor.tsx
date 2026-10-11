import type { ClientWriteRequest } from "../../api/generated/models";
import { isValidRut } from "../../format";
import { Button, ValidatedForm } from "../../ui";

export const customerKinds: Record<string, string> = {
  PERSON: "Persona natural",
  COMPANY: "Empresa",
  UNKNOWN: "Tipo sin registrar",
};

export function ClientEditor({
  value,
  setValue,
  busy,
  historicalRut,
  onSave,
  onCancel,
}: {
  value: ClientWriteRequest;
  setValue: (value: ClientWriteRequest) => void;
  busy: boolean;
  historicalRut?: string;
  onSave: () => void;
  onCancel: () => void;
}): JSX.Element {
  const contacts = value.contacts ?? [],
    addresses = value.addresses ?? [];
  const rutInvalid = Boolean(value.rut) && value.rut !== historicalRut && !isValidRut(value.rut!);
  return (
    <ValidatedForm
      className="customer-editor"
      onSubmit={(event) => {
        event.preventDefault();
        if (!rutInvalid) onSave();
      }}
    >
      <fieldset disabled={busy}>
        <legend>{historicalRut === undefined ? "Nuevo cliente" : "Editar ficha"}</legend>
        <div className="customer-fields">
          <label>
            Tipo
            <select
              value={value.party_kind ?? "UNKNOWN"}
              onChange={(event) =>
                setValue({
                  ...value,
                  party_kind: event.target.value as ClientWriteRequest["party_kind"],
                })
              }
            >
              {Object.entries(customerKinds).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          {(
            [
              ["name", "Nombre o razón social"],
              ["rut", "RUT"],
              ["giro", "Giro"],
              ["address", "Dirección de facturación"],
              ["comuna", "Comuna de facturación"],
            ] as const
          ).map(([key, label]) => (
            <label key={key}>
              {label}
              <input
                name={key}
                required={key === "name"}
                maxLength={
                  key === "address" ? 2000 : key === "comuna" ? 20 : key === "giro" ? 80 : 255
                }
                value={value[key] ?? ""}
                onChange={(event) => setValue({ ...value, [key]: event.target.value })}
              />
            </label>
          ))}
        </div>
        {rutInvalid && <p role="alert">Revisa el RUT y su dígito verificador.</p>}
        <h3>Contactos</h3>
        <p>
          El contacto principal se propone al crear una obra. Los demás quedan disponibles en la
          ficha.
        </p>
        {contacts.map((contact, index) => (
          <div className="customer-child" key={contact.id ?? index}>
            {(
              [
                ["name", "Nombre del contacto"],
                ["contact_role", "Rol del contacto"],
                ["email", "Correo"],
                ["phone", "Teléfono"],
              ] as const
            ).map(([key, label]) => (
              <label key={key}>
                {label}
                <input
                  type={key === "email" ? "email" : "text"}
                  value={contact[key] ?? ""}
                  maxLength={key === "contact_role" ? 80 : key === "phone" ? 64 : 255}
                  onChange={(event) =>
                    setValue({
                      ...value,
                      contacts: contacts.map((item, i) =>
                        i === index ? { ...item, [key]: event.target.value } : item,
                      ),
                    })
                  }
                />
              </label>
            ))}
            <label>
              <input
                type="radio"
                name="primary-contact"
                checked={contact.is_primary ?? false}
                onChange={() =>
                  setValue({
                    ...value,
                    contacts: contacts.map((item, i) => ({ ...item, is_primary: i === index })),
                  })
                }
              />
              Principal
            </label>
            <Button
              onClick={() =>
                setValue({ ...value, contacts: contacts.filter((_, i) => i !== index) })
              }
            >
              Quitar contacto {index + 1}
            </Button>
          </div>
        ))}
        <Button
          onClick={() =>
            setValue({
              ...value,
              contacts: [
                ...contacts,
                { name: "", contact_role: "", email: "", phone: "", is_primary: !contacts.length },
              ],
            })
          }
        >
          Agregar contacto
        </Button>
        <h3>Direcciones de obra</h3>
        <p>
          Elegir una dirección copia su texto al proyecto. Una edición posterior de esta ficha no
          cambia lo emitido.
        </p>
        {addresses.map((address, index) => (
          <div className="customer-child" key={address.id ?? index}>
            {(
              [
                ["label", "Nombre de la obra o dirección"],
                ["address", "Dirección de obra"],
                ["comuna", "Comuna"],
              ] as const
            ).map(([key, label]) => (
              <label key={key}>
                {label}
                <input
                  required={key !== "comuna"}
                  value={address[key] ?? ""}
                  maxLength={key === "address" ? 500 : 80}
                  onChange={(event) =>
                    setValue({
                      ...value,
                      addresses: addresses.map((item, i) =>
                        i === index ? { ...item, [key]: event.target.value } : item,
                      ),
                    })
                  }
                />
              </label>
            ))}
            <Button
              onClick={() =>
                setValue({ ...value, addresses: addresses.filter((_, i) => i !== index) })
              }
            >
              Quitar dirección {index + 1}
            </Button>
          </div>
        ))}
        <Button
          onClick={() =>
            setValue({
              ...value,
              addresses: [...addresses, { label: "", address: "", comuna: "" }],
            })
          }
        >
          Agregar dirección de obra
        </Button>
        <div className="customer-actions">
          <Button type="submit" variant="primary" disabled={busy || rutInvalid}>
            {busy ? "Guardando ficha" : "Guardar cliente"}
          </Button>
          <Button onClick={onCancel} disabled={busy}>
            Cancelar
          </Button>
        </div>
      </fieldset>
    </ValidatedForm>
  );
}
