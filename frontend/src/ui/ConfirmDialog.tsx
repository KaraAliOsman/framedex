import {
  createContext,
  type PropsWithChildren,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from "react";

import { t } from "../i18n/es-CL";

import { Dialog } from "./Dialog";

export type ConfirmRequest = {
  title: string;
  body?: string;
  confirmLabel?: string;
  danger?: boolean;
  /** When set, the surface asks for a text value instead of a yes/no. */
  input?: { label?: string; placeholder?: string };
};

type ConfirmFn = (request: ConfirmRequest) => Promise<boolean>;
type PromptFn = (request: ConfirmRequest) => Promise<string | null>;

const ConfirmContext = createContext<ConfirmFn | null>(null);
const PromptContext = createContext<PromptFn | null>(null);

/** Drop-in replacement for `window.confirm`: `if (!(await confirm({title, body}))) return;` */
export function useConfirm(): ConfirmFn {
  const confirm = useContext(ConfirmContext);
  if (!confirm) throw new Error("useConfirm must be used within <ConfirmProvider>");
  return confirm;
}

/** Drop-in replacement for `window.prompt`: resolves the trimmed text or null on cancel. */
export function usePrompt(): PromptFn {
  const prompt = useContext(PromptContext);
  if (!prompt) throw new Error("usePrompt must be used within <ConfirmProvider>");
  return prompt;
}

type PendingRequest = {
  request: ConfirmRequest;
  resolve: (value: boolean | string | null) => void;
};

export function ConfirmProvider({ children }: PropsWithChildren): JSX.Element {
  // Requests queue: a second confirmation while one is open must not strand
  // the first caller — it waits for its own dialog, shown next.
  const queueRef = useRef<PendingRequest[]>([]);
  const [current, setCurrent] = useState<PendingRequest | null>(null);
  const [draft, setDraft] = useState("");
  const request = current?.request ?? null;

  const enqueue = useCallback(
    (next: ConfirmRequest): Promise<boolean | string | null> =>
      new Promise<boolean | string | null>((resolve) => {
        queueRef.current.push({ request: next, resolve });
        setCurrent((previous) => previous ?? queueRef.current.shift() ?? null);
        setDraft("");
      }),
    [],
  );

  const confirm = useCallback<ConfirmFn>(async (next) => Boolean(await enqueue(next)), [enqueue]);

  const prompt = useCallback<PromptFn>(
    (next) => enqueue({ ...next, input: next.input ?? {} }) as Promise<string | null>,
    [enqueue],
  );

  const settle = useCallback(
    (value: boolean) => {
      const answer = request?.input ? (value ? draft.trim() : null) : value;
      current?.resolve(answer);
      setCurrent(queueRef.current.shift() ?? null);
      setDraft("");
    },
    [current, draft, request],
  );

  const api = useMemo(() => confirm, [confirm]);
  const promptApi = useMemo(() => prompt, [prompt]);

  return (
    <ConfirmContext.Provider value={api}>
      <PromptContext.Provider value={promptApi}>
        {children}
        {request ? (
          <Dialog
            footer={
              <>
                <button onClick={() => settle(false)} type="button">
                  {t("ui.cancel")}
                </button>
                <button
                  className={request.danger ? "ui-button--danger" : "ui-button--primary"}
                  data-primary
                  disabled={Boolean(request.input) && !draft.trim()}
                  onClick={() => settle(true)}
                  type="button"
                >
                  {request.confirmLabel ?? t("ui.confirm")}
                </button>
              </>
            }
            onClose={() => settle(false)}
            title={request.title}
            width="s"
          >
            {request.body ? <p className="ui-dialog__text">{request.body}</p> : null}
            {request.input ? (
              <label className="ui-field">
                {request.input.label ? (
                  <span className="ui-field__label">{request.input.label}</span>
                ) : null}
                <input
                  autoFocus
                  className="ui-field__input"
                  onChange={(event) => setDraft(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && draft.trim()) settle(true);
                  }}
                  placeholder={request.input.placeholder}
                  value={draft}
                />
              </label>
            ) : null}
          </Dialog>
        ) : null}
      </PromptContext.Provider>
    </ConfirmContext.Provider>
  );
}
