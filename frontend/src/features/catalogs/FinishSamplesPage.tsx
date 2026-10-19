import { useEffect, useMemo, useRef, useState } from "react";
import { useQueries, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError, apiFetchBlob } from "../../api/apiMutator";
import {
  engineSystems,
  finishReferencesArchive,
  finishReferencesCreate,
  finishReferencesList,
  finishReferencesUpdate,
  getFinishReferencesImageUrl,
  projectDesignOptions,
} from "../../api/generated/dekopen";
import type { FinishReference } from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { Button, DeniedState, EmptyState, Loading, useConfirm } from "../../ui";
import { Icon } from "../../ui/Icon";
import { actionErrorDetail } from "../errors";
import "./finish-samples.css";

type Grain = "ALONG" | "ACROSS" | "NONE";
const GRAIN_LABEL: Record<Grain, string> = {
  ALONG: "A lo largo del perfil",
  ACROSS: "Atravesada",
  NONE: "Sin dirección",
};

/** Catálogos › Muestras propias (encargo O15): the company's own photo of a
 * material, cropped to a repeatable square, with its physical size and grain.
 * It dresses an existing catalog finish in drawings — it never changes the
 * finish code, its price or any fabrication value, and certifies no colour. */
export function FinishSamplesPage(): JSX.Element {
  const auth = useAuthSession();
  const org = auth.me?.active_organization;
  if (!org) return <DeniedState reason="Elige tu organización para ver sus muestras." />;
  const canEdit = org.role === "OWNER" || org.role === "ESTIMATOR";
  const canRead = canEdit || org.role === "WORKSHOP_MANAGER";
  if (!canRead)
    return <DeniedState reason="El dueño, el estimador o el jefe de taller ven las muestras." />;
  return <FinishSamples key={org.id} orgId={org.id} canEdit={canEdit} />;
}

function useFinishChoices(orgId: string) {
  const systems = useQuery({
    queryKey: ["project-systems", orgId],
    queryFn: async () => {
      const response = await engineSystems({ headers: { "X-Organization-ID": orgId } });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data.systems;
    },
    staleTime: 60_000,
  });
  const options = useQueries({
    queries: (systems.data ?? []).map((system) => ({
      queryKey: ["project-design-options", orgId, system.id],
      staleTime: 60_000,
      queryFn: async () => {
        const response = await projectDesignOptions(system.id, {
          headers: { "X-Organization-ID": orgId },
        });
        if (response.status !== 200) throw new ApiError(response.status, response.data);
        return response.data;
      },
    })),
  });
  return useMemo(() => {
    const byCode = new Map<string, { code: string; name: string; systems: string[] }>();
    options.forEach((result, index) => {
      const system = systems.data?.[index];
      for (const color of result.data?.finish_authority?.colors ?? []) {
        const entry = byCode.get(color.code) ?? { code: color.code, name: color.name, systems: [] };
        if (system && !entry.systems.includes(system.name)) entry.systems.push(system.name);
        byCode.set(color.code, entry);
      }
    });
    return [...byCode.values()].sort((a, b) => a.name.localeCompare(b.name, "es-CL"));
  }, [options, systems.data]);
}

function useImage(orgId: string, item: FinishReference | null): string | null {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    if (!item) return;
    let alive = true;
    let created: string | null = null;
    void apiFetchBlob(getFinishReferencesImageUrl(item.id), {
      headers: { "X-Organization-ID": orgId },
    })
      .then(({ blob }) => {
        created = URL.createObjectURL(blob);
        if (alive) setUrl(created);
      })
      .catch(() => alive && setUrl(null));
    return () => {
      alive = false;
      if (created) URL.revokeObjectURL(created);
    };
  }, [orgId, item?.id, item?.version]); // eslint-disable-line react-hooks/exhaustive-deps
  return url;
}

function FinishSamples({ orgId, canEdit }: { orgId: string; canEdit: boolean }): JSX.Element {
  const client = useQueryClient();
  const [adding, setAdding] = useState(false);
  const list = useQuery({
    queryKey: ["finish-references", orgId],
    queryFn: async () => {
      const response = await finishReferencesList({ headers: { "X-Organization-ID": orgId } });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data.items;
    },
  });
  const choices = useFinishChoices(orgId);
  const nameOf = (code: string) => choices.find((item) => item.code === code)?.name ?? code;
  const refresh = () => client.invalidateQueries({ queryKey: ["finish-references", orgId] });
  const emptyLibrary = list.isSuccess && list.data.length === 0 && adding === false;
  return (
    <section className="finish-samples" aria-labelledby="page-title">
      <header className="finish-samples__head">
        <div>
          <h1 id="page-title">Muestras propias</h1>
          <p>
            Fotos de tus materiales para que el dibujo y la propuesta se vean como tu producto. No
            cambian el acabado del catálogo, su precio ni sus medidas.
          </p>
        </div>
        {canEdit && !adding ? (
          <Button variant="primary" icon={<Icon name="upload" />} onClick={() => setAdding(true)}>
            Subir muestra
          </Button>
        ) : null}
      </header>
      {adding ? (
        <SampleUpload
          orgId={orgId}
          choices={choices}
          onCancel={() => setAdding(false)}
          onSaved={() => {
            setAdding(false);
            void refresh();
          }}
        />
      ) : null}
      {list.isPending ? (
        <Loading label="Cargando muestras" />
      ) : list.isError ? (
        <p role="alert">No se pudieron leer las muestras.</p>
      ) : emptyLibrary ? (
        <EmptyState
          title="Aún no hay muestras propias"
          body="Sube una foto del foliado o el color que vendes; la verás en las ventanas que usen ese acabado."
          action={
            canEdit ? (
              <Button variant="primary" onClick={() => setAdding(true)}>
                Subir muestra
              </Button>
            ) : undefined
          }
        />
      ) : (
        <ul className="sample-grid">
          {list.data.map((item) => (
            <SampleCard
              key={item.id}
              orgId={orgId}
              item={item}
              finishName={nameOf(item.finish_code)}
              canEdit={canEdit}
              onChanged={() => void refresh()}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

function FramePreview({
  url,
  tileMm,
  size = 180,
}: {
  url: string | null;
  tileMm: number;
  size?: number;
}) {
  // The frame shows ~1200 mm of profile, so the sample repeats at its physical size.
  const scale = Math.max(8, Math.round((size * tileMm) / 1200));
  return (
    <span
      className="sample-frame"
      style={{
        width: size,
        height: size,
        backgroundImage: url ? `url(${url})` : undefined,
        backgroundSize: `${scale}px ${scale}px`,
      }}
      aria-hidden="true"
    >
      <span className="sample-frame__glass" />
    </span>
  );
}

function SampleCard({
  orgId,
  item,
  finishName,
  canEdit,
  onChanged,
}: {
  orgId: string;
  item: FinishReference;
  finishName: string;
  canEdit: boolean;
  onChanged(): void;
}): JSX.Element {
  const url = useImage(orgId, item);
  const confirm = useConfirm();
  const [editing, setEditing] = useState(false);
  const [tile, setTile] = useState(item.tile_mm);
  const [grain, setGrain] = useState<Grain>(item.grain as Grain);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function save(): Promise<void> {
    setBusy(true);
    setError("");
    try {
      const response = await finishReferencesUpdate(
        item.id,
        { tile_mm: tile, grain },
        { headers: { "X-Organization-ID": orgId } },
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setEditing(false);
      onChanged();
    } catch {
      setError("No se pudo guardar. Revisa el tamaño (20 a 3000 mm).");
    } finally {
      setBusy(false);
    }
  }
  async function archive(): Promise<void> {
    if (
      !(await confirm({
        title: `¿Quitar la muestra «${item.name}»?`,
        body: "Las ventanas volverán a dibujarse con el color del catálogo. La foto original se conserva.",
        danger: true,
      }))
    )
      return;
    setBusy(true);
    try {
      await finishReferencesArchive(item.id, { headers: { "X-Organization-ID": orgId } });
      onChanged();
    } finally {
      setBusy(false);
    }
  }
  return (
    <li className="sample-card">
      <FramePreview url={url} tileMm={Number(editing ? tile : item.tile_mm)} />
      <div className="sample-card__body">
        <strong>{item.name}</strong>
        <span>Se ve como {finishName}</span>
        <span className="sample-card__meta">
          Muestra de {Number(item.tile_mm).toLocaleString("es-CL")} mm ·{" "}
          {GRAIN_LABEL[item.grain as Grain]} · versión {item.version}
        </span>
        <span className="sample-card__tag">Referencia del negocio</span>
      </div>
      {editing ? (
        <div className="sample-card__edit">
          <label className="ui-field">
            <span className="ui-field__label">Tamaño de la muestra (mm)</span>
            <input
              className="ui-field__input"
              inputMode="decimal"
              value={tile}
              onChange={(event) => setTile(event.target.value)}
            />
          </label>
          <label className="ui-field">
            <span className="ui-field__label">Veta</span>
            <select
              className="ui-field__input"
              value={grain}
              onChange={(event) => setGrain(event.target.value as Grain)}
            >
              {(Object.keys(GRAIN_LABEL) as Grain[]).map((value) => (
                <option key={value} value={value}>
                  {GRAIN_LABEL[value]}
                </option>
              ))}
            </select>
          </label>
          <div className="sample-card__actions">
            <Button variant="primary" loading={busy} onClick={() => void save()}>
              Guardar
            </Button>
            <Button onClick={() => setEditing(false)} disabled={busy}>
              Cancelar
            </Button>
          </div>
          {error ? <p role="alert">{error}</p> : null}
        </div>
      ) : canEdit ? (
        <div className="sample-card__actions">
          <Button size="compact" onClick={() => setEditing(true)}>
            Ajustar
          </Button>
          <Button size="compact" variant="ghost" disabled={busy} onClick={() => void archive()}>
            Quitar
          </Button>
        </div>
      ) : null}
    </li>
  );
}

function SampleUpload({
  orgId,
  choices,
  onCancel,
  onSaved,
}: {
  orgId: string;
  choices: { code: string; name: string; systems: string[] }[];
  onCancel(): void;
  onSaved(): void;
}): JSX.Element {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [tile, setTile] = useState("300");
  const [grain, setGrain] = useState<Grain>("ALONG");
  const [zoom, setZoom] = useState(100);
  const [x, setX] = useState(50);
  const [y, setY] = useState(50);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (!file) return;
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);
  const tileNumber = Number(tile.replace(",", "."));
  const valid = Boolean(file && name.trim() && code && tileNumber >= 20 && tileNumber <= 3000);
  async function save(): Promise<void> {
    if (!file || !valid) return;
    setBusy(true);
    setError("");
    try {
      const response = await finishReferencesCreate(
        {
          file,
          name: name.trim(),
          finish_code: code,
          tile_mm: String(tileNumber),
          grain,
          x: String(x / 100),
          y: String(y / 100),
          size: String(zoom / 100),
        },
        { headers: { "X-Organization-ID": orgId } },
      );
      if (response.status !== 201) throw new ApiError(response.status, response.data);
      onSaved();
    } catch (caught) {
      setError(
        actionErrorDetail(
          caught,
          "No se pudo guardar la muestra. Revisa el archivo y vuelve a intentarlo.",
        ),
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="sample-upload" aria-label="Nueva muestra">
      <div className="sample-upload__media">
        {preview ? (
          <>
            <div
              className="sample-crop"
              style={{
                backgroundImage: `url(${preview})`,
                backgroundSize: `${10000 / zoom}%`,
                backgroundPosition: `${x}% ${y}%`,
              }}
              role="img"
              aria-label="Recorte cuadrado de la muestra"
            />
            <FramePreview url={preview} tileMm={tileNumber || 300} size={140} />
          </>
        ) : (
          <button type="button" className="sample-drop" onClick={() => input.current?.click()}>
            <Icon name="image" size={24} />
            Elegir foto del material
            <small>PNG, JPEG o WebP · hasta 8 MB</small>
          </button>
        )}
        <input
          ref={input}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          className="sr-only"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
      </div>
      <div className="sample-upload__fields">
        <label className="ui-field">
          <span className="ui-field__label">Nombre</span>
          <input
            className="ui-field__input"
            value={name}
            maxLength={120}
            placeholder="p. ej. Nogal de nuestro proveedor"
            onChange={(event) => setName(event.target.value)}
          />
        </label>
        <label className="ui-field">
          <span className="ui-field__label">Se ve como (acabado del catálogo)</span>
          <select
            className="ui-field__input"
            value={code}
            onChange={(event) => setCode(event.target.value)}
          >
            <option value="">Elegir acabado</option>
            {choices.map((choice) => (
              <option key={choice.code} value={choice.code}>
                {choice.name} · {choice.systems.join(", ")}
              </option>
            ))}
          </select>
        </label>
        <div className="sample-upload__row">
          <label className="ui-field">
            <span className="ui-field__label">Tamaño real de la muestra (mm)</span>
            <input
              className="ui-field__input"
              inputMode="decimal"
              value={tile}
              onChange={(event) => setTile(event.target.value)}
            />
          </label>
          <label className="ui-field">
            <span className="ui-field__label">Veta</span>
            <select
              className="ui-field__input"
              value={grain}
              onChange={(event) => setGrain(event.target.value as Grain)}
            >
              {(Object.keys(GRAIN_LABEL) as Grain[]).map((value) => (
                <option key={value} value={value}>
                  {GRAIN_LABEL[value]}
                </option>
              ))}
            </select>
          </label>
        </div>
        {preview ? (
          <fieldset className="sample-upload__crop">
            <legend>Recorte</legend>
            <label>
              Acercar
              <input
                type="range"
                min={20}
                max={100}
                value={zoom}
                onChange={(event) => setZoom(Number(event.target.value))}
              />
            </label>
            <label>
              Horizontal
              <input
                type="range"
                min={0}
                max={100}
                value={x}
                onChange={(event) => setX(Number(event.target.value))}
              />
            </label>
            <label>
              Vertical
              <input
                type="range"
                min={0}
                max={100}
                value={y}
                onChange={(event) => setY(Number(event.target.value))}
              />
            </label>
            <button
              type="button"
              className="ui-button ui-button--ghost ui-button--compact"
              onClick={() => input.current?.click()}
            >
              Cambiar foto
            </button>
          </fieldset>
        ) : null}
        <p className="sample-upload__note">
          La foto sirve para presentación. No certifica un color RAL ni reemplaza la muestra del
          fabricante.
        </p>
        {error ? <p role="alert">{error}</p> : null}
        <div className="sample-upload__actions">
          <Button variant="primary" loading={busy} disabled={!valid} onClick={() => void save()}>
            Guardar muestra
          </Button>
          <Button onClick={onCancel} disabled={busy}>
            Cancelar
          </Button>
        </div>
      </div>
    </section>
  );
}
