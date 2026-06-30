"use client";

import { useState, useEffect, useCallback } from "react";

export type ThemePreference = "system" | "light" | "dark";
type ResolvedTheme = "light" | "dark";

const STORAGE_KEY = "letrascopio-theme";

function applyTheme(resolved: ResolvedTheme) {
  if (resolved === "dark") {
    document.documentElement.classList.add("dark");
  } else {
    document.documentElement.classList.remove("dark");
  }
}

function getSystemPreference(): ResolvedTheme {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function resolveTheme(pref: ThemePreference): ResolvedTheme {
  if (pref === "system") return getSystemPreference();
  return pref;
}

export function useTheme() {
  const [preference, setPreference] = useState<ThemePreference>("system");
  const [resolved, setResolved] = useState<ResolvedTheme>("light");

  useEffect(() => {
    // Leer preferencia guardada (el inline script en layout.tsx ya aplicó la clase)
    const saved = localStorage.getItem(STORAGE_KEY) as ThemePreference | null;
    const pref = saved ?? "system";
    const res = resolveTheme(pref);
    setPreference(pref);
    setResolved(res);

    // Escuchar cambios del sistema si la preferencia es "system"
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handleSystem = () => {
      setPreference((prev) => {
        if (prev === "system") {
          const r = getSystemPreference();
          setResolved(r);
          applyTheme(r);
        }
        return prev;
      });
    };
    mq.addEventListener("change", handleSystem);
    return () => mq.removeEventListener("change", handleSystem);
  }, []);

  const setTheme = useCallback((pref: ThemePreference) => {
    const res = resolveTheme(pref);
    setPreference(pref);
    setResolved(res);
    applyTheme(res);
    try {
      localStorage.setItem(STORAGE_KEY, pref);
    } catch {
      // silenciar errores de storage en SSR / incognito
    }
  }, []);

  // Compatibilidad: toggleTheme alterna entre light y dark (ignora system)
  const toggleTheme = useCallback(() => {
    setTheme(resolved === "dark" ? "light" : "dark");
  }, [resolved, setTheme]);

  return {
    theme: preference,
    setTheme,
    toggleTheme,
    isDark: resolved === "dark",
    resolved,
  };
}
