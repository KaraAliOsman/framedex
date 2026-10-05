import {
  createContext,
  type PropsWithChildren,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Dialog } from "./Dialog";
import { TextInput } from "./Controls";

export type Command = {
  id: string;
  label: string;
  keywords?: readonly string[];
  shortcut?: string;
  disabledReason?: string;
  run: () => void | Promise<void>;
};
const Registry = createContext<{
  commands: readonly Command[];
  register: (commands: readonly Command[]) => () => void;
} | null>(null);
export function CommandProvider({ children }: PropsWithChildren): JSX.Element {
  const entries = useRef(new Map<string, Command>());
  const [commands, setCommands] = useState<Command[]>([]);
  const register = useCallback((next: readonly Command[]) => {
    next.forEach((command) => entries.current.set(command.id, command));
    setCommands(Array.from(entries.current.values()));
    return () => {
      next.forEach((command) => {
        if (entries.current.get(command.id) === command) entries.current.delete(command.id);
      });
      setCommands(Array.from(entries.current.values()));
    };
  }, []);
  const value = useMemo(() => ({ commands, register }), [commands, register]);
  return <Registry.Provider value={value}>{children}</Registry.Provider>;
}
export function useCommandRegistry(): NonNullable<React.ContextType<typeof Registry>> {
  const registry = useContext(Registry);
  if (!registry) throw new Error("CommandProvider is required");
  return registry;
}
export function CommandPalette(): JSX.Element {
  const { commands } = useCommandRegistry();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const id = "dekopen-command-search";
  const normalized = query
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("es-CL");
  const results = commands.filter((command) =>
    [command.label, ...(command.keywords ?? [])].some((text) =>
      text
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLocaleLowerCase("es-CL")
        .includes(normalized),
    ),
  );
  const selected = results[Math.min(active, results.length - 1)];
  useEffect(() => {
    const key = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
        setQuery("");
        setActive(0);
        setError(null);
      }
    };
    document.addEventListener("keydown", key);
    return () => document.removeEventListener("keydown", key);
  }, []);
  async function execute(command: Command): Promise<void> {
    if (busy || command.disabledReason) return;
    setBusy(true);
    setError(null);
    try {
      await command.run();
      setOpen(false);
    } catch {
      setError("No se pudo ejecutar el comando. Revisa los datos y vuelve a intentar.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <button
        className="ui-button"
        type="button"
        title="Buscar comandos — Ctrl+K"
        onClick={() => {
          setOpen(true);
          setQuery("");
          setError(null);
        }}
      >
        Buscar comandos <kbd>Ctrl+K</kbd>
      </button>
      {open ? (
        <Dialog
          title="Comandos"
          onClose={() => {
            if (!busy) setOpen(false);
          }}
          width="m"
          surface="palette"
        >
          <TextInput
            autoFocus
            aria-label="Buscar comando"
            aria-controls={id}
            aria-activedescendant={selected ? `command-${selected.id}` : undefined}
            role="combobox"
            aria-expanded="true"
            aria-autocomplete="list"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setActive(0);
            }}
            onKeyDown={(event) => {
              if (["ArrowDown", "ArrowUp"].includes(event.key)) {
                event.preventDefault();
                setActive(
                  (previous) =>
                    (previous + (event.key === "ArrowDown" ? 1 : -1) + results.length) %
                    (results.length || 1),
                );
              }
              if (event.key === "Enter") {
                event.preventDefault();
                event.stopPropagation();
                if (selected) void execute(selected);
              }
            }}
          />
          <div
            className="ui-command-list"
            role="listbox"
            id={id}
            aria-label="Comandos disponibles"
            aria-busy={busy}
          >
            {results.map((command) => (
              <div
                key={command.id}
                id={`command-${command.id}`}
                role="option"
                aria-selected={selected?.id === command.id}
                aria-disabled={Boolean(command.disabledReason)}
              >
                <button
                  type="button"
                  className="ui-menu__item"
                  disabled={busy || Boolean(command.disabledReason)}
                  title={command.disabledReason}
                  onClick={() => void execute(command)}
                >
                  {command.label}
                  {command.shortcut ? <kbd>{command.shortcut}</kbd> : null}
                </button>
                {command.disabledReason ? <span>{command.disabledReason}</span> : null}
              </div>
            ))}
            {!results.length ? <p role="status">Sin comandos que coincidan.</p> : null}
          </div>
          {error ? <p role="alert">{error}</p> : null}
          <p className="ui-command-help">↑↓ recorrer · Enter ejecutar · Esc cerrar</p>
        </Dialog>
      ) : null}
    </>
  );
}
