import { MoonStar, SunMedium } from "lucide-react";

import { useThemeStore } from "@/stores/theme.store";

export const ThemeToggle = () => {
  const { theme, toggleTheme } = useThemeStore();
  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="button-secondary gap-2"
      aria-label="Toggle dark mode"
    >
      {theme === "dark" ? <SunMedium className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
      {theme === "dark" ? "Light mode" : "Dark mode"}
    </button>
  );
};

