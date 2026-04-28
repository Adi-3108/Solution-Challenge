import { create } from "zustand";

type ThemeMode = "light" | "dark";

type ThemeState = {
  theme: ThemeMode;
  toggleTheme: () => void;
  setTheme: (theme: ThemeMode) => void;
};

const applyTheme = (theme: ThemeMode): void => {
  if (typeof document === "undefined") {
    return;
  }
  document.documentElement.classList.toggle("dark", theme === "dark");
  if (typeof window !== "undefined") {
    window.localStorage.setItem("fairsight-theme", theme);
  }
};

const savedTheme =
  typeof window !== "undefined"
    ? ((window.localStorage.getItem("fairsight-theme") as ThemeMode | null) ?? "light")
    : "light";

applyTheme(savedTheme);

export const useThemeStore = create<ThemeState>((set) => ({
  theme: savedTheme,
  toggleTheme: () =>
    set((state) => {
      const nextTheme: ThemeMode = state.theme === "dark" ? "light" : "dark";
      applyTheme(nextTheme);
      return { theme: nextTheme };
    }),
  setTheme: (theme) => {
    applyTheme(theme);
    set({ theme });
  },
}));
