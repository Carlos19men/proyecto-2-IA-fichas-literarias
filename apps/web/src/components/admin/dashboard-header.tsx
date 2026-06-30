"use client";

import { Button } from "@/components/ui/button";
import { Moon, Sun, Bell, Search, User } from "lucide-react";
import { useTheme } from "@/lib/theme";

export function DashboardHeader() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 w-full items-center justify-between px-6">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <span className="font-bold text-primary-foreground text-sm">LS</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold font-playfair">LetraScopio Admin</h1>
            <p className="text-xs text-muted-foreground">
              Panel de Administración
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="relative hidden md:block">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="search"
              placeholder="Buscar fichas, usuarios..."
              className="h-10 w-64 rounded-lg border border-border bg-background pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-ring text-foreground"
            />
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            aria-label="Cambiar tema"
          >
            {theme === "dark" ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </Button>

          <Button variant="ghost" size="icon" className="relative" aria-label="Notificaciones">
            <Bell className="h-5 w-5" />
            <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-xs text-destructive-foreground">
              3
            </span>
          </Button>

          <Button variant="ghost" className="gap-2" aria-label="Perfil de administrador">
            <User className="h-5 w-5" />
            <span className="hidden sm:inline">Administrador</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
