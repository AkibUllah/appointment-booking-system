import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from 'react';

export interface Toast { id: number; kind: 'success' | 'error' | 'info'; message: string }

interface ToastApi { toasts: Toast[]; push: (kind: Toast['kind'], message: string) => void; dismiss: (id: number) => void }

const ToastContext = createContext<ToastApi | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const counter = useRef(0);
  const dismiss = useCallback((id: number) => setToasts((t) => t.filter((x) => x.id !== id)), []);
  const push = useCallback(
    (kind: Toast['kind'], message: string) => {
      const id = ++counter.current;
      setToasts((t) => [...t, { id, kind, message }]);
      window.setTimeout(() => dismiss(id), 4500);
    },
    [dismiss],
  );
  const value = useMemo(() => ({ toasts, push, dismiss }), [toasts, push, dismiss]);
  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>;
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside ToastProvider');
  return ctx;
}

const styles: Record<Toast['kind'], string> = {
  success: 'border-brand-500 bg-brand-50 text-brand-700',
  error: 'border-red-300 bg-red-50 text-red-700',
  info: 'border-slate-300 bg-white text-slate-700',
};

export function ToastViewport() {
  const { toasts, dismiss } = useToast();
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2" aria-live="polite">
      {toasts.map((t) => (
        <button
          key={t.id}
          type="button"
          onClick={() => dismiss(t.id)}
          className={`pointer-events-auto rounded-md border px-4 py-3 text-left text-sm shadow ${styles[t.kind]}`}
        >
          {t.message}
        </button>
      ))}
    </div>
  );
}
