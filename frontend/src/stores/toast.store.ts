import { create } from "zustand";

export type ToastRecord = {
  id: string;
  title: string;
  description: string;
  tone: "info" | "error";
};

type ToastState = {
  toasts: ToastRecord[];
  addToast: (toast: Omit<ToastRecord, "id">) => void;
  removeToast: (id: string) => void;
};

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  addToast: (toast) =>
    set((state) => ({
      toasts: [...state.toasts, { ...toast, id: crypto.randomUUID() }],
    })),
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((toast) => toast.id !== id),
    })),
}));

