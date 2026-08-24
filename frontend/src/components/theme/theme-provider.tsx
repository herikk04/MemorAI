import * as React from "react";

type Theme = "dark" | "light" | "system";

type ThemeProviderState = {
  theme: Theme;
  resolvedTheme: "dark" | "light";
  setTheme: (theme: Theme) => void;
  toggle: () => void;
};

const ThemeProviderContext = React.createContext<ThemeProviderState | undefined>(
  undefined
);

const STORAGE_KEY = "memorai-theme";

function getSystemTheme(): "dark" | "light" {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function readStoredTheme(): Theme {
  if (typeof window === "undefined") return "system";
  const stored = window.localStorage.getItem(STORAGE_KEY) as Theme | null;
  return stored ?? "system";
}

function applyThemeClass(theme: "dark" | "light") {
  const root = window.document.documentElement;
  root.classList.remove("light", "dark");
  root.classList.add(theme);
  root.style.colorScheme = theme;
}

export function ThemeProvider({
  children,
  defaultTheme = "system",
}: {
  children: React.ReactNode;
  defaultTheme?: Theme;
}) {
  const [theme, setThemeState] = React.useState<Theme>(
    () => readStoredTheme() ?? defaultTheme
  );
  const [resolvedTheme, setResolvedTheme] = React.useState<"dark" | "light">(
    () => getSystemTheme()
  );

  React.useEffect(() => {
    const resolved = theme === "system" ? getSystemTheme() : theme;
    applyThemeClass(resolved);
    setResolvedTheme(resolved);
  }, [theme]);

  React.useEffect(() => {
    if (theme !== "system") return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      const next = getSystemTheme();
      applyThemeClass(next);
      setResolvedTheme(next);
    };
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [theme]);

  const setTheme = React.useCallback((next: Theme) => {
    window.localStorage.setItem(STORAGE_KEY, next);
    setThemeState(next);
  }, []);

  const toggle = React.useCallback(() => {
    setThemeState((prev) => {
      const current = prev === "system" ? getSystemTheme() : prev;
      const next: Theme = current === "dark" ? "light" : "dark";
      window.localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  }, []);

  const value = { theme, resolvedTheme, setTheme, toggle };
  return (
    <ThemeProviderContext.Provider value={value}>
      {children}
    </ThemeProviderContext.Provider>
  );
}

export function useTheme(): ThemeProviderState {
  const context = React.useContext(ThemeProviderContext);
  if (!context)
    throw new Error("useTheme deve ser usado dentro de <ThemeProvider>");
  return context;
}
