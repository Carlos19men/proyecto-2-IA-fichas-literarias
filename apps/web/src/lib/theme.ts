"use client";

import { useState, useEffect, useCallback } from "react";

type Theme = "light" | "dark";

const STORAGE_KEY = "letrascopio-theme";

export function useTheme() {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    // Leer el estado actual del DOM (ya fue aplicado por el inline script en layout.tsx)
    const isDark = document.documentElement.classList.contains("dark");
    setTheme(isDark ? "dark" : "light");
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => {
      const next: Theme = prev === "light" ? "dark" : "light";
      if (next === "dark") {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch (e) {
        // silenciar errores de storage en SSR / incognito
      }
      return next;
    });
  }, []);

  return { theme, toggleTheme, isDark: theme === "dark" };
}
