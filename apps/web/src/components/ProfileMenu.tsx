"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useTheme, ThemePreference } from "@/lib/theme";
import { useRouter } from "next/navigation";

export interface ProfileMenuProps {
  /** Si el sidebar está colapsado (solo muestra avatar) */
  collapsed?: boolean;
  /** Datos del usuario logueado. null = no logueado */
  user?: { name: string; subtitle?: string; initials: string } | null;
  /** Si el usuario tiene permisos de admin */
  isAdmin?: boolean;
  /** Callback para login (cuando no hay sesión) */
  onLogin?: () => void;
  /** Callback para logout */
  onLogout?: () => void;
  /** Dirección de apertura del popover */
  popoverDirection?: "above" | "below";
}

const THEME_OPTIONS: { value: ThemePreference; label: string; icon: React.ReactNode }[] = [
  { value: "system", label: "Sistema", icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg> },
  { value: "light", label: "Claro", icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg> },
  { value: "dark", label: "Oscuro", icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg> },
];

const POPOVER_WIDTH = 260;

export function ProfileMenu({
  collapsed = false,
  user = null,
  isAdmin = false,
  onLogin,
  onLogout,
  popoverDirection = "above",
}: ProfileMenuProps) {
  const { theme, setTheme, isDark } = useTheme();
  const router = useRouter();

  const [open, setOpen] = useState(false);
  const [themeSubOpen, setThemeSubOpen] = useState(false);
  const [popoverStyle, setPopoverStyle] = useState<React.CSSProperties>({});
  const menuRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  // Calcula la posición del popover usando coordenadas del viewport (position: fixed)
  const calcPosition = useCallback(() => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const vw = window.innerWidth;

    if (popoverDirection === "above") {
      // Sidebar: abre hacia arriba, alineado a la izquierda del trigger
      setPopoverStyle({
        position: "fixed",
        bottom: window.innerHeight - rect.top + 8,
        left: Math.max(8, rect.left),
        width: POPOVER_WIDTH,
      });
    } else {
      // Header: abre hacia abajo, alineado al borde derecho del trigger
      const right = vw - rect.right;
      setPopoverStyle({
        position: "fixed",
        top: rect.bottom + 8,
        right: Math.max(8, right),
        width: POPOVER_WIDTH,
      });
    }
  }, [popoverDirection]);

  const handleToggle = () => {
    if (!open) calcPosition();
    setOpen((v) => !v);
    setThemeSubOpen(false);
  };

  // Cerrar al hacer clic fuera
  useEffect(() => {
    if (!open) return;
    function handleClickOutside(e: MouseEvent) {
      if (
        menuRef.current &&
        !menuRef.current.contains(e.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
        setThemeSubOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  // Recalcular si la ventana cambia de tamaño
  useEffect(() => {
    if (!open) return;
    window.addEventListener("resize", calcPosition);
    return () => window.removeEventListener("resize", calcPosition);
  }, [open, calcPosition]);

  const handleThemeSelect = (val: ThemePreference) => {
    setTheme(val);
    setThemeSubOpen(false);
    setOpen(false);
  };

  const handleAdminClick = () => {
    setOpen(false);
    router.push("/admin");
  };

  return (
    <div style={{ position: "relative" }}>
      {/* ── Trigger button ── */}
      <button
        ref={triggerRef}
        id="profile-menu-trigger"
        onClick={handleToggle}
        aria-label={user ? "Abrir menú de perfil" : "Iniciar sesión"}
        aria-expanded={open}
        style={{
          display: "flex",
          alignItems: "center",
          gap: collapsed ? 0 : 10,
          width: "100%",
          padding: "8px 10px",
          borderRadius: 12,
          border: "none",
          background: open ? "var(--color-accent-muted)" : "transparent",
          cursor: "pointer",
          transition: "background 0.15s ease",
          textAlign: "left",
          color: "var(--color-text-primary)",
        }}
        onMouseEnter={(e) => {
          if (!open) (e.currentTarget as HTMLButtonElement).style.background = "var(--color-accent-muted)";
        }}
        onMouseLeave={(e) => {
          if (!open) (e.currentTarget as HTMLButtonElement).style.background = "transparent";
        }}
      >
        {/* Avatar */}
        <div
          style={{
            width: 34,
            height: 34,
            borderRadius: "50%",
            background: user ? "var(--color-accent)" : "var(--color-bg-card)",
            border: "2px solid var(--color-border)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          {user ? (
            <span style={{ fontSize: "0.8125rem", fontWeight: 700, color: "#fff", letterSpacing: "0.02em" }}>
              {user.initials}
            </span>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          )}
        </div>

        {/* Name + subtitle */}
        {!collapsed && (
          <div style={{ flex: 1, overflow: "hidden" }}>
            <div style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--color-text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {user ? user.name : "Iniciar sesión"}
            </div>
            {user?.subtitle && (
              <div style={{ fontSize: "0.6875rem", color: "var(--color-text-muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {user.subtitle}
              </div>
            )}
          </div>
        )}

        {/* Gear icon */}
        {!collapsed && user && (
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
        )}
      </button>

      {/* ── Popover (position: fixed para no quedar recortado por overflow) ── */}
      {open && (
        <div
          ref={menuRef}
          role="menu"
          style={{
            ...popoverStyle,
            background: isDark ? "#1E2028" : "#fff",
            border: "1px solid var(--color-border)",
            borderRadius: 14,
            boxShadow: isDark
              ? "0 8px 40px rgba(0,0,0,0.55)"
              : "0 8px 32px rgba(46,94,133,0.14)",
            padding: "6px 0",
            zIndex: 99999,
            animation: "fadeSlideUp 0.15s ease forwards",
          }}
        >
          {/* User header en el popover */}
          {user && (
            <div style={{ padding: "10px 16px 8px", display: "flex", alignItems: "center", gap: 10, borderBottom: "1px solid var(--color-border)", marginBottom: 4 }}>
              <div style={{ width: 38, height: 38, borderRadius: "50%", background: "var(--color-accent)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <span style={{ color: "#fff", fontWeight: 700, fontSize: "0.875rem" }}>{user.initials}</span>
              </div>
              <div>
                <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--color-text-primary)" }}>{user.name}</div>
                {user.subtitle && <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>{user.subtitle}</div>}
              </div>
            </div>
          )}

          {/* Actividad (solo si está logueado) */}
          {user && (
            <MenuItem
              icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>}
              label="Actividad"
              onClick={() => setOpen(false)}
            />
          )}

          {/* Tema con submenú */}
          <div style={{ position: "relative" }}>
            <MenuItem
              icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" /></svg>}
              label="Tema"
              right={
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              }
              onClick={() => setThemeSubOpen((v) => !v)}
            />
            {themeSubOpen && (
              <div style={{
                position: "absolute",
                ...(popoverDirection === "above" ? { left: "calc(100% + 4px)" } : { right: "calc(100% + 4px)", left: "auto" }),
                top: 0,
                width: 140,
                background: isDark ? "#1E2028" : "#fff",
                border: "1px solid var(--color-border)",
                borderRadius: 10,
                boxShadow: isDark ? "0 4px 24px rgba(0,0,0,0.5)" : "0 4px 20px rgba(46,94,133,0.12)",
                padding: "4px 0",
                zIndex: 100000,
              }}>
                {THEME_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => handleThemeSelect(opt.value)}
                    style={{
                      display: "flex", alignItems: "center", justifyContent: "space-between",
                      width: "100%", padding: "9px 14px", background: "transparent",
                      border: "none", cursor: "pointer", fontSize: "0.8125rem",
                      color: "var(--color-text-primary)", borderRadius: 7, transition: "background 0.12s",
                    }}
                    onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--color-accent-muted)")}
                    onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "transparent")}
                  >
                    <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      {opt.icon}
                      {opt.label}
                    </span>
                    {theme === opt.value && (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Admin — solo si está logueado Y es admin */}
          {isAdmin && user && (
            <MenuItem
              icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></svg>}
              label="Administrar Fichas"
              onClick={handleAdminClick}
            />
          )}

          {/* Separador */}
          <div style={{ height: 1, background: "var(--color-border)", margin: "4px 0" }} />

          {/* Login / Logout */}
          {user ? (
            <MenuItem
              icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></svg>}
              label="Cerrar sesión"
              onClick={() => { setOpen(false); onLogout?.(); }}
            />
          ) : (
            <MenuItem
              icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" /><polyline points="10 17 15 12 10 7" /><line x1="15" y1="12" x2="3" y2="12" /></svg>}
              label="Iniciar sesión"
              labelStyle={{ color: "var(--color-accent)", fontWeight: 600 }}
              onClick={() => { setOpen(false); onLogin?.(); }}
            />
          )}
        </div>
      )}
    </div>
  );
}

// ── Shared menu item ────────────────────────────────────────────────
function MenuItem({
  icon,
  label,
  right,
  onClick,
  labelStyle,
}: {
  icon: React.ReactNode;
  label: string;
  right?: React.ReactNode;
  onClick?: () => void;
  labelStyle?: React.CSSProperties;
}) {
  return (
    <button
      role="menuitem"
      onClick={onClick}
      style={{
        display: "flex", alignItems: "center", gap: 10,
        width: "100%", padding: "9px 16px",
        background: "transparent", border: "none", cursor: "pointer",
        fontSize: "0.8125rem", color: "var(--color-text-primary)",
        transition: "background 0.12s", textAlign: "left",
      }}
      onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "var(--color-accent-muted)")}
      onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "transparent")}
    >
      <span style={{ color: "var(--color-text-muted)", display: "flex" }}>{icon}</span>
      <span style={{ flex: 1, ...labelStyle }}>{label}</span>
      {right && <span style={{ color: "var(--color-text-muted)", display: "flex" }}>{right}</span>}
    </button>
  );
}
