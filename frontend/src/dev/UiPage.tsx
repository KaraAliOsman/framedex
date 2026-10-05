import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { catalogSystemList, projectsList } from "../api/generated/dekopen";
import { ApiError } from "../api/apiMutator";
import { useAuthSession } from "../auth/AuthSessionProvider";
import { useProject } from "../features/projects/useProject";
import { domainLabel } from "../i18n/domainLabels";
import { useTheme } from "../theme/ThemeProvider";
import {
  Area,
  BlockedState,
  Button,
  ButtonGroup,
  Checkbox,
  Combobox,
  CommandPalette,
  CommandProvider,
  ContextMenu,
  DataTable,
  DateOnly,
  DemoBadge,
  DeniedState,
  Dialog,
  DimLoader,
  Dims,
  Drawer,
  EmptyState,
  EntityCode,
  ErrorState,
  Field,
  Icon,
  IconButton,
  InlineEdit,
  Inspector,
  KeyValue,
  Length,
  LoadingState,
  Menu,
  Money,
  MoneyField,
  NumberField,
  OpeningGlyph,
  Panel,
  Percent,
  Popover,
  Qty,
  Radio,
  Section,
  SegmentedControl,
  Select,
  SheetSurface,
  Stat,
  StatusChip,
  Stepper,
  Switch,
  Tabs,
  TechDetails,
  TextField,
  Timestamp,
  Tooltip,
  TraceButton,
  UnknownValue,
  Uvalue,
  ValidatedForm,
  Weight,
  useCommandRegistry,
  useConfirm,
  useToast,
  type IconKind,
  type OpeningKind,
  type TableColumn,
  type TableState,
} from "../ui";
import type { ProjectResponse } from "../api/generated/models";
import "./ui.css";

const openings: readonly OpeningKind[] = [
  "FIXED",
  "TURN_LEFT",
  "TURN_RIGHT",
  "TILT",
  "TILT_TURN_LEFT",
  "TILT_TURN_RIGHT",
  "AWNING",
  "SLIDING_2L",
  "DOOR",
];
const densities = [
  { value: "office", label: "Oficina" },
  { value: "workshop", label: "Taller" },
  { value: "document", label: "Documento" },
];
const stateOptions = ["ready", "empty", "loading", "error", "denied", "blocked"].map(
  (value, index) => ({
    value,
    label: ["Datos", "Vacío", "Carga", "Error", "Sin permiso", "Bloqueado"][index]!,
  }),
);
const columns: TableColumn<ProjectResponse>[] = [
  {
    id: "code",
    label: "Código",
    value: (row) => row.code,
    render: (row) => <EntityCode kind="proyecto" code={row.code} />,
  },
  { id: "name", label: "Obra", value: (row) => row.name },
  {
    id: "status",
    label: "Estado",
    value: (row) => domainLabel(row.status),
    render: (row) => <StatusChip status={row.status} />,
  },
  { id: "quantity", label: "Vanos", value: (row) => row.position_count, numeric: true },
  {
    id: "total",
    label: "Total",
    value: (row) => (row.pricing_current ? row.total_price_gross : null),
    numeric: true,
    render: (row) =>
      row.pricing_current ? (
        <Money value={row.total_price_gross} currency={row.currency} />
      ) : (
        <UnknownValue cause="Falta aplicar precios" />
      ),
  },
];

export function UiPage(): JSX.Element {
  return (
    <CommandProvider>
      <Manual />
    </CommandProvider>
  );
}

function Manual(): JSX.Element {
  const auth = useAuthSession();
  const orgId = auth.me?.active_organization?.id ?? "";
  const { theme, toggleTheme } = useTheme();
  const [density, setDensity] = useState("office");
  const [tab, setTab] = useState("manual");
  const [number, setNumber] = useState("");
  const [amount, setAmount] = useState("");
  const [text, setText] = useState("");
  const [choice, setChoice] = useState("FIXED");
  const [checked, setChecked] = useState(false);
  const [radio, setRadio] = useState("interior");
  const [tableMode, setTableMode] = useState("ready");
  const [overlay, setOverlay] = useState<"dialog" | "drawer" | null>(null);
  const [selectedProject, setSelectedProject] = useState("");
  const [feedback, setFeedback] = useState("");
  const [localSelection, setLocalSelection] = useState<readonly string[]>([]);
  const { notify } = useToast();
  const confirm = useConfirm();
  const { register } = useCommandRegistry();
  const list = useQuery({
    queryKey: ["ui-manual-projects", orgId],
    enabled: Boolean(orgId),
    queryFn: async ({ signal }) => {
      const response = await projectsList({ signal, headers: { "X-Organization-ID": orgId } });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data.items;
    },
  });
  const project = useProject(selectedProject || list.data?.[0]?.id || null);
  const systems = useQuery({
    queryKey: ["ui-manual-systems", orgId],
    enabled: Boolean(orgId),
    queryFn: async ({ signal }) => {
      const response = await catalogSystemList({ signal, headers: { "X-Organization-ID": orgId } });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data.items;
    },
  });
  const position = project.data?.positions?.[0];
  const system = systems.data?.find((item) => item.id === position?.design.system_id);
  const glass = position?.bom.glasses[0];
  const weight = position?.bom.leaf_weights[0];
  const openingOptions = openings.map((value) => ({
    value,
    label: value === "TILT" ? "Abatimiento" : domainLabel(value),
  }));
  const retry = () => {
    setTableMode("ready");
    void list.refetch();
  };
  const tableState: TableState =
    tableMode === "loading"
      ? { kind: "loading" }
      : tableMode === "error"
        ? {
            kind: "error",
            cause:
              "El estado de ejemplo permite comprobar la recuperación. Los datos provienen de la API.",
            retry,
          }
        : tableMode === "denied"
          ? { kind: "denied", role: "Estimador", contact: "la persona dueña de tu organización" }
          : tableMode === "blocked"
            ? {
                kind: "blocked",
                cause: "Falta seleccionar una obra para consultar sus medidas.",
                action: <Button onClick={() => setTableMode("ready")}>Volver a las obras</Button>,
              }
            : list.isPending
              ? { kind: "loading" }
              : list.isError
                ? {
                    kind: "error",
                    cause: "No se pudieron consultar las obras de tu organización.",
                    retry,
                  }
                : { kind: "ready" };
  useEffect(() => {
    const original = document.documentElement.dataset.density;
    document.documentElement.dataset.density = density;
    return () => {
      if (original) document.documentElement.dataset.density = original;
      else delete document.documentElement.dataset.density;
    };
  }, [density]);
  useEffect(
    () =>
      register([
        { id: "theme", label: "Cambiar tema", shortcut: "Ctrl+K", run: toggleTheme },
        { id: "drawer", label: "Abrir ficha de la obra", run: () => setOverlay("drawer") },
        { id: "document", label: "Usar densidad de documento", run: () => setDensity("document") },
      ]),
    [register, toggleTheme],
  );
  const inspectorGroups = useMemo(
    () => [
      {
        id: "source",
        title: "Fuente",
        content: (
          <dl>
            <KeyValue label="Obra">
              <EntityCode kind="proyecto" code={project.data?.code} />
            </KeyValue>
            <KeyValue label="Revisión">{project.data?.current_revision ?? "Sin dato"}</KeyValue>
            <KeyValue label="Sistema">{system?.code ?? "Sin dato"}</KeyValue>
          </dl>
        ),
      },
      {
        id: "dimensions",
        title: "Medidas declaradas",
        content: (
          <dl>
            <KeyValue label="Ancho">
              <Length mm={position?.design.nominal_width_mm} />
            </KeyValue>
            <KeyValue label="Alto">
              <Length mm={position?.design.nominal_height_mm} />
            </KeyValue>
            <KeyValue label="Cantidad">
              <Qty value={position?.quantity} />
            </KeyValue>
            <KeyValue label="Vidrio">
              <Area m2={glass?.area_m2} />
            </KeyValue>
            <KeyValue label="Peso">
              <Weight
                kg={weight?.total_weight_kg}
                cause="El catálogo no declara todas las masas de la hoja"
              />
            </KeyValue>
          </dl>
        ),
      },
      {
        id: "authority",
        title: "Autoridad",
        advanced: true,
        content: (
          <>
            <UnknownValue cause="DEMO_60 no acredita fabricación ni certificación térmica" />
            <TechDetails
              summary="Detalles técnicos · huella del cálculo"
              diagnostic={position?.bom.calculation_hash ?? "Sin dato"}
            />
          </>
        ),
      },
    ],
    [project.data, position, glass, weight, system],
  );
  return (
    <main className="ui-manual" data-density={density} data-theme={theme}>
      <header className="ui-manual__header" data-region="manual-configuracion">
        <div>
          <p className="ui-spec-label">DEKOPEN / MATERIAL DE INTERFAZ / V2</p>
          <h1>Manual de componentes</h1>
          <p>Una línea, una fuente, una decisión.</p>
        </div>
        <div className="ui-manual__settings">
          <SegmentedControl
            label="Densidad"
            value={density}
            options={densities}
            onValueChange={setDensity}
          />
          <Button onClick={toggleTheme}>Tema {theme === "light" ? "oscuro" : "claro"}</Button>
          <CommandPalette />
        </div>
      </header>
      <Tabs
        label="Láminas del manual"
        value={tab}
        onChange={setTab}
        items={[
          { id: "manual", label: "Componentes" },
          { id: "comparison", label: "Bien / Mal" },
        ]}
      />
      {tab === "comparison" ? (
        <section className="ui-manual__comparison" aria-label="Bien y Mal">
          <div className="ui-manual__bad" data-example="mal">
            <span>Mal · referencia histórica board-06</span>
            <h2>Todo compite</h2>
            <p>Tarjetas blandas, brillos y números sin fuente impiden reconocer la decisión.</p>
            <div className="ui-manual__bad-card">
              Tres acciones compiten / cuatro métricas decorativas / ninguna autoridad
            </div>
            <p>Esta muestra gráfica no ejecuta acciones ni contiene resultados de ingeniería.</p>
          </div>
          <SheetSurface miter>
            <p className="ui-spec-label">Bien · gramática del taller</p>
            <h2>{project.data?.name ?? "Seleccione una obra"}</h2>
            <p>
              <DemoBadge /> Fuente: API de tu organización
            </p>
            <Dims w={position?.design.nominal_width_mm} h={position?.design.nominal_height_mm} />
            <p>Vista interior</p>
            <OpeningGlyph type="TURN_LEFT" />
            <TraceButton
              trace={null}
              cause="La respuesta actual del motor entrega su huella; todavía no adjunta fórmula ni versión como traza"
            />
            <ButtonGroup region="comparacion-accion">
              <Button variant="primary" onClick={() => setTab("manual")}>
                Revisar la ficha
              </Button>
            </ButtonGroup>
          </SheetSurface>
        </section>
      ) : (
        <>
          <SheetSurface miter className="ui-manual__sheet">
            <div>
              <p className="ui-spec-label">01 / Fuente y cifras</p>
              <h2>{project.data?.name ?? "Obra de tu organización"}</h2>
              <DemoBadge />
              <Field label="Obra de referencia">
                <Select
                  value={selectedProject || list.data?.[0]?.id || ""}
                  onChange={(event) => setSelectedProject(event.target.value)}
                  options={(list.data ?? []).map((row) => ({
                    value: row.id,
                    label: `${row.code} · ${row.name}`,
                  }))}
                  emptyMessage="No hay obras; crea el fixture local para comprobar cifras"
                />
              </Field>
              <p>
                Vista interior · Las cifras se leen del backend. Los campos de abajo son entradas de
                presentación y no modifican la obra.
              </p>
              <Dims w={position?.design.nominal_width_mm} h={position?.design.nominal_height_mm} />
              <dl className="ui-manual__values">
                <KeyValue label="Precio">
                  {project.data?.pricing_current ? (
                    <Money
                      value={project.data.total_price_gross}
                      currency={project.data.currency}
                    />
                  ) : (
                    <UnknownValue cause="Falta aplicar precios a la obra" />
                  )}
                </KeyValue>
                <KeyValue label="Área de vidrio">
                  <Area m2={glass?.area_m2} />
                </KeyValue>
                <KeyValue label="Peso">
                  <Weight
                    kg={weight?.total_weight_kg}
                    cause="El catálogo no declara todas las masas de la hoja"
                  />
                </KeyValue>
                <KeyValue label="Transmitancia">
                  <Uvalue value={null} cause="El catálogo DEMO no aporta certificación térmica" />
                </KeyValue>
                <KeyValue label="Cantidad">
                  <Qty value={position?.quantity} />
                </KeyValue>
                <KeyValue label="Descuento">
                  <Percent value={position?.discount_pct} kind="points" />
                </KeyValue>
                <KeyValue label="Actualización">
                  <Timestamp value={project.data?.updated_at} />
                </KeyValue>
                <KeyValue label="Fecha">
                  <DateOnly value={project.data?.updated_at?.slice(0, 10)} />
                </KeyValue>
              </dl>
              <TraceButton
                trace={null}
                cause="El contrato actual adjunta la huella del cálculo, sin fórmula ni versión; consulta Detalles técnicos"
              />
              <TechDetails
                summary="Detalles técnicos · huella del cálculo"
                diagnostic={position?.bom.calculation_hash ?? "Sin dato"}
              />
            </div>
            <Inspector groups={inspectorGroups} />
          </SheetSurface>
          <Panel title="02 / Acciones">
            <ButtonGroup region="manual-acciones">
              <Button
                variant="primary"
                onClick={() => notify("Acción registrada en el muestrario")}
              >
                Registrar acción
              </Button>
              <Button onClick={() => setOverlay("drawer")}>Abrir ficha</Button>
              <Button variant="ghost" onClick={() => setFeedback("Acción secundaria registrada")}>
                Acción secundaria
              </Button>
              <Button
                variant="danger"
                onClick={() =>
                  void confirm({
                    title: "¿Limpiar las entradas del muestrario?",
                    body: "Se borran solo los campos de esta lámina. La obra conserva sus datos.",
                    confirmLabel: "Limpiar entradas",
                    danger: true,
                  }).then((accepted) => {
                    if (accepted) {
                      setNumber("");
                      setAmount("");
                      setText("");
                      notify("Entradas limpiadas");
                    }
                  })
                }
              >
                Limpiar entradas
              </Button>
              <IconButton
                label="Abrir diálogo"
                shortcut="Enter"
                icon={<Icon kind="info" />}
                onClick={() => setOverlay("dialog")}
              />
              <Button size="sm" onClick={() => setFeedback("Control denso activado")}>
                Denso
              </Button>
              <Button size="touch" onClick={() => setFeedback("Control táctil activado")}>
                Táctil
              </Button>
              <Button disabled disabledReason="Falta seleccionar una revisión emitida">
                No disponible
              </Button>
              <Button loading>Procesando</Button>
            </ButtonGroup>
            <p role="status">{feedback}</p>
            <DimLoader progress={65} label="Avance de muestra: 65 por ciento" />
          </Panel>
          <Section title="03 / Entradas de presentación">
            <ValidatedForm
              className="ui-manual__fields"
              onSubmit={(event) => {
                event.preventDefault();
                notify("Formato válido; no se modificó la obra");
              }}
            >
              <Field
                label="Nombre de muestra"
                required
                help="Etiqueta persistente y validación en español"
              >
                <TextField
                  name="name"
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                />
              </Field>
              <Field label="Medida" required help="Acepta 2400, 2 400, 2.400 o 1249,5">
                <NumberField
                  name="dimension"
                  value={number}
                  onValueChange={setNumber}
                  decimals={1}
                  suffix="mm"
                />
              </Field>
              <Field label="Monto en pesos" required>
                <MoneyField name="amount" currency="CLP" value={amount} onValueChange={setAmount} />
              </Field>
              <Field label="Correo de muestra">
                <TextField name="email" type="email" />
              </Field>
              <Combobox
                label="Apertura"
                value={choice}
                options={openingOptions}
                onValueChange={setChoice}
              />
              <Field label="Selección">
                <Select
                  value={choice}
                  options={openingOptions}
                  onChange={(event) => setChoice(event.target.value)}
                />
              </Field>
              <Checkbox
                label="Mostrar notas"
                checked={checked}
                onChange={(event) => setChecked(event.target.checked)}
              />
              <div role="group" aria-label="Vista">
                <Radio
                  label="Vista interior"
                  name="view"
                  checked={radio === "interior"}
                  onChange={() => setRadio("interior")}
                />
                <Radio
                  label="Vista exterior"
                  name="view"
                  checked={radio === "exterior"}
                  onChange={() => setRadio("exterior")}
                />
              </div>
              <SwitchRow checked={checked} change={setChecked} />
              <div>
                <InlineEdit
                  ariaLabel="Nota local"
                  placeholder="Agregar una nota"
                  value={text}
                  onCommit={setText}
                />
              </div>
              <Button type="submit" variant="primary">
                Comprobar formato
              </Button>
            </ValidatedForm>
            {checked ? (
              <p role="note">
                Las entradas son locales; el backend mantiene la autoridad de los valores.
              </p>
            ) : null}
          </Section>
          <Panel title="04 / Tabla y ciclo">
            <SegmentedControl
              label="Estado de la tabla"
              value={tableMode}
              options={stateOptions}
              onValueChange={setTableMode}
            />
            <DataTable
              rows={tableMode === "empty" ? [] : (list.data ?? [])}
              columns={columns}
              rowKey={(row) => row.id}
              label="obras"
              state={tableState}
              emptyReason="Crea una obra con el fixture local para probar la tabla."
              emptyAction={
                <a className="ui-button" href="/projects">
                  Abrir proyectos
                </a>
              }
              selectionActions={(ids) => (
                <Button
                  onClick={() => {
                    setLocalSelection(ids);
                    setOverlay("drawer");
                  }}
                >
                  Revisar selección
                </Button>
              )}
            />
            <Stepper
              current="calculated"
              steps={[
                { id: "draft", label: "Borrador" },
                { id: "calculated", label: "Evaluado" },
                {
                  id: "issued",
                  label: "Emitido",
                  disabledReason: "Estado de ejemplo; no emite documentos",
                  onSelect: () => setFeedback("Revisa la emisión desde el proyecto"),
                },
              ]}
            />
            <Stat
              label="Vanos en esta obra"
              value={<Qty value={project.data?.position_count} />}
              decision={{ label: "Revisar vanos", onClick: () => setOverlay("drawer") }}
            />
          </Panel>
          <Panel title="05 / Gramática de aperturas">
            <p>
              Vista {radio === "interior" ? "interior" : "exterior"} · continuo hacia el observador,
              discontinuo alejándose.
            </p>
            <div className="ui-manual__glyphs">
              {openings.map((type) => (
                <figure key={type}>
                  <OpeningGlyph type={type} view={radio as "interior" | "exterior"} />
                  <figcaption>{type === "TILT" ? "Abatimiento" : domainLabel(type)}</figcaption>
                </figure>
              ))}
            </div>
            <div className="ui-manual__glyphs">
              {[
                "check",
                "warning",
                "stop",
                "clock",
                "profile",
                "dimension",
                "mullion",
                "transom",
                "cut",
              ].map((kind) => (
                <Icon key={kind} kind={kind as IconKind} />
              ))}
            </div>
            <ButtonGroup region="manual-estados">
              {["DRAFT", "QUOTED", "APPROVED", "BLOCKED", "FAILED", "SUCCEEDED"].map((status) => (
                <StatusChip key={status} status={status} />
              ))}
            </ButtonGroup>
          </Panel>
          <Panel title="06 / Capas">
            <ButtonGroup region="manual-capas">
              <Popover label="Procedencia" trigger={<Button>Ver procedencia</Button>}>
                <p>Datos del fixture mediante la API autenticada.</p>
              </Popover>
              <Menu
                label="Acciones de la ficha"
                items={[
                  { id: "review", label: "Revisar ficha", onSelect: () => setOverlay("drawer") },
                  {
                    id: "source",
                    label: "Abrir proyecto",
                    href: project.data ? `/projects/${project.data.id}` : "/projects",
                  },
                ]}
              />
              <Tooltip text="Comprobar la fuente — Enter">
                <Button onClick={() => setFeedback("Fuente: API autenticada de la organización")}>
                  Comprobar fuente
                </Button>
              </Tooltip>
            </ButtonGroup>
            <ContextMenu
              label="Área con menú contextual"
              items={[
                { id: "inspect", label: "Inspeccionar", onSelect: () => setOverlay("drawer") },
              ]}
            >
              <p>Clic derecho o Mayús+F10: inspeccionar la ficha.</p>
            </ContextMenu>
          </Panel>
          <Panel title="07 / Los cinco estados">
            <EmptyState
              title="Todavía no hay una selección"
              body="Selecciona una obra para revisar su información."
              action={<Button onClick={() => setOverlay("drawer")}>Revisar selección</Button>}
            />
            <LoadingState label="Consultando la fuente" />
            <ErrorState
              title="No se pudo consultar la fuente"
              body="Esta lámina representa el estado de error y ofrece recuperación."
              onRetry={retry}
              technical="Estado de ejemplo del muestrario"
            />
            <DeniedState reason="Esta operación requiere el rol Estimador; pídelo a la persona dueña de tu organización." />
            <BlockedState
              reason="Falta evidencia del sistema antes de fabricar."
              action={
                <a className="ui-button" href="/catalogs/systems">
                  Revisar catálogo
                </a>
              }
            />
          </Panel>
        </>
      )}
      {overlay === "dialog" ? (
        <Dialog
          title="Ficha técnica del componente"
          onClose={() => setOverlay(null)}
          footer={<Button onClick={() => setOverlay(null)}>Cerrar ficha</Button>}
        >
          <p>El diálogo conserva el foco y vuelve al control que lo abrió.</p>
          <EntityCode kind="proyecto" code={project.data?.code} />
        </Dialog>
      ) : null}
      {overlay === "drawer" ? (
        <Drawer title="Ficha de la obra" onClose={() => setOverlay(null)}>
          <p>{project.data?.name ?? "Sin obra seleccionada"}</p>
          <p>
            {localSelection.length
              ? `${localSelection.length} obras seleccionadas para revisar`
              : "Consulta de datos; no aplica cambios en lote"}
          </p>
          <Dims w={position?.design.nominal_width_mm} h={position?.design.nominal_height_mm} />
          <UnknownValue cause="La evidencia DEMO no autoriza fabricación" />
          <a
            className="ui-button"
            href={project.data ? `/projects/${project.data.id}` : "/projects"}
          >
            Abrir proyecto
          </a>
        </Drawer>
      ) : null}
    </main>
  );
}

function SwitchRow({
  checked,
  change,
}: {
  checked: boolean;
  change: (value: boolean) => void;
}): JSX.Element {
  return <Switch label="Notas de procedencia" checked={checked} onCheckedChange={change} />;
}
