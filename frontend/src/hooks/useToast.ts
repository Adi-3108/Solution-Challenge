import { useCallback } from "react";

import { useToastStore } from "@/stores/toast.store";

export const useToast = () => {
  const { addToast, removeToast, toasts } = useToastStore();

  const showError = useCallback(
    (title: string, description: string) => addToast({ title, description, tone: "error" }),
    [addToast],
  );

  const showInfo = useCallback(
    (title: string, description: string) => addToast({ title, description, tone: "info" }),
    [addToast],
  );

  return {
    toasts,
    removeToast,
    showError,
    showInfo,
  };
};

