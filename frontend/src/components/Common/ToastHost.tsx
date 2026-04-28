import { useEffect } from "react";
import { AlertTriangle, Info } from "lucide-react";

import { useToastStore } from "@/stores/toast.store";

export const ToastHost = () => {
  const { toasts, removeToast } = useToastStore();

  useEffect(() => {
    const timers = toasts.map((toast) =>
      window.setTimeout(() => {
        removeToast(toast.id);
      }, 4500),
    );
    return () => {
      timers.forEach((timer) => window.clearTimeout(timer));
    };
  }, [removeToast, toasts]);

  return (
    <div className="fixed right-4 top-4 z-50 flex w-full max-w-sm flex-col gap-3">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className="panel flex items-start gap-3 border-l-4 border-l-brand-600 p-4 shadow-panel"
        >
          {toast.tone === "error" ? (
            <AlertTriangle className="mt-0.5 h-5 w-5 text-rose-600" />
          ) : (
            <Info className="mt-0.5 h-5 w-5 text-brand-600" />
          )}
          <div className="space-y-1">
            <p className="font-semibold text-slate-950 dark:text-white">{toast.title}</p>
            <p className="text-sm text-slate-600 dark:text-slate-300">{toast.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
};

