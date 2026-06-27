"use client";

import { useState } from "react";
import { useTheme } from "@/lib/theme";
import { MOCK_CONVERSATIONS } from "@/lib/mock-data";
import { useRouter } from "next/navigation";

interface SidebarProps {
  activeConvId: string | null;
  onSelectConv: (id: string) => void;
  onNewConv: () => void;
}

export function Sidebar({ activeConvId, onSelectConv, onNewConv }: SidebarProps) {
  const { isDark, toggleTheme } = useTheme();
  const [collapsed, setCollapsed] = useState(false);
  const router = useRouter();

  const [conversations, setConversations] = useState(() =>
    MOCK_CONVERSATIONS.map(c => ({ ...c, isPinned: false }))
  );

  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");

  const togglePin = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setConversations((prev) => {
      const idx = prev.findIndex((c) => c.id === id);
      if (idx === -1) return prev;
      const newConvs = [...prev];
      const conv = { ...newConvs[idx], isPinned: !newConvs[idx].isPinned };
      newConvs[idx] = conv;
      return newConvs.sort((a, b) => {
        if (a.isPinned && !b.isPinned) return -1;
        if (!a.isPinned && b.isPinned) return 1;
        return 0;
      });
    });
  };

  const deleteConv = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (activeConvId === id) {
      onNewConv();
    }
  };

  const renameConv = (id: string, newTitle: string) => {
    if (newTitle.trim()) {
      setConversations((prev) =>
        prev.map(c => c.id === id ? { ...c, title: newTitle.trim() } : c)
      );
    }
    setRenamingId(null);
  };

  // TODO: Reemplazar con lógica de autenticación real
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isAdmin, setIsAdmin] = useState(true); // Para probar la vista de admin

  return (
    <aside
      style={{
        width: collapsed ? 60 : 260,
        minWidth: collapsed ? 60 : 260,
        background: "var(--color-bg-secondary)",
        borderRight: "1px solid var(--color-border)",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        transition: "width 0.25s ease, min-width 0.25s ease",
        overflow: "hidden",
      }}
    >
      {/* Logo + collapse toggle */}
      <div
        className="flex items-center justify-between px-4 py-4"
        style={{ borderBottom: "1px solid var(--color-border)", minHeight: 60 }}
      >
        {!collapsed && (
          <button
            onClick={() => router.push("/")}
            className="font-playfair font-bold"
            style={{
              fontSize: "1.125rem",
              color: "var(--color-accent)",
              background: "none",
              border: "none",
              cursor: "pointer",
              padding: 0,
              letterSpacing: "-0.02em",
            }}
          >
            LetraScopio
          </button>
        )}
        <button
          onClick={() => setCollapsed((c) => !c)}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            color: "var(--color-text-muted)",
            padding: 4,
            borderRadius: 6,
            display: "flex",
            alignItems: "center",
            transition: "color 0.2s",
          }}
          aria-label={collapsed ? "Expandir sidebar" : "Colapsar sidebar"}
          title={collapsed ? "Expandir" : "Colapsar"}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            {collapsed ? (
              <>
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </>
            ) : (
              <>
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </>
            )}
          </svg>
        </button>
      </div>

      {/* New conversation button */}
      <div className="p-3" style={{ borderBottom: "1px solid var(--color-border)" }}>
        <button
          id="new-conv-btn"
          onClick={onNewConv}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            gap: collapsed ? 0 : 8,
            justifyContent: collapsed ? "center" : "flex-start",
            padding: "10px 12px",
            borderRadius: 10,
            background: "var(--color-accent-muted)",
            border: "1.5px solid var(--color-accent)",
            color: "var(--color-accent)",
            fontWeight: 600,
            fontSize: "0.875rem",
            cursor: "pointer",
            transition: "all 0.2s",
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          {!collapsed && "Nueva conversación"}
        </button>
      </div>

      {/* Conversation list */}
      {!collapsed && (
        <nav className="flex-1 overflow-y-auto p-3 flex flex-col gap-1 relative">
          <p
            style={{ fontSize: "0.6875rem", fontWeight: 700, color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", padding: "4px 8px 8px" }}
          >
            Historial
          </p>
          {menuOpenId && (
            <div
              className="fixed inset-0 z-10"
              onClick={(e) => { e.stopPropagation(); setMenuOpenId(null); }}
            />
          )}
          {conversations.map((conv) => (
            <div
              key={conv.id}
              id={`conv-${conv.id}`}
              onClick={() => {
                if (renamingId !== conv.id) {
                  onSelectConv(conv.id);
                }
              }}
              className="group relative"
              style={{
                width: "100%",
                textAlign: "left",
                padding: "8px 8px",
                borderRadius: 10,
                background: activeConvId === conv.id ? "var(--color-accent-muted)" : "transparent",
                border: activeConvId === conv.id ? "1px solid var(--color-border)" : "1px solid transparent",
                color: activeConvId === conv.id ? "var(--color-accent)" : "var(--color-text-primary)",
                cursor: renamingId === conv.id ? "default" : "pointer",
                transition: "all 0.15s",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 4,
              }}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: 2, overflow: "hidden", flex: 1 }}>
                <span style={{ fontSize: "0.875rem", fontWeight: 500, display: "flex", alignItems: "center", gap: 6, width: "100%" }}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, opacity: 0.6 }}>
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  </svg>

                  {renamingId === conv.id ? (
                    <input
                      type="text"
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") renameConv(conv.id, renameValue);
                        if (e.key === "Escape") setRenamingId(null);
                      }}
                      onBlur={() => renameConv(conv.id, renameValue)}
                      autoFocus
                      onClick={(e) => e.stopPropagation()}
                      style={{
                        background: "var(--color-bg-primary)",
                        border: "1px solid var(--color-accent)",
                        borderRadius: 4,
                        padding: "2px 4px",
                        fontSize: "0.875rem",
                        color: "var(--color-text-primary)",
                        width: "100%",
                        outline: "none",
                      }}
                    />
                  ) : (
                    <span className="truncate" style={{ flex: 1, maxWidth: 160 }}>{conv.title}</span>
                  )}

                  {conv.isPinned && renamingId !== conv.id && (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, color: "var(--color-text-muted)" }}>
                      <line x1="12" y1="17" x2="12" y2="22" />
                      <path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 11.24V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3v5.24a2 2 0 0 1-1.11 1.31l-1.78.9A2 2 0 0 0 5 15.24Z" />
                    </svg>
                  )}
                </span>
                {renamingId !== conv.id && (
                  <span style={{ fontSize: "0.6875rem", color: "var(--color-text-muted)", paddingLeft: 18 }}>{conv.date}</span>
                )}
              </div>

              {/* Three dots menu */}
              {renamingId !== conv.id && (
                <div style={{ flexShrink: 0, position: "relative" }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setMenuOpenId(menuOpenId === conv.id ? null : conv.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                    style={{
                      background: "none",
                      border: "none",
                      padding: 4,
                      cursor: "pointer",
                      color: "var(--color-text-muted)",
                      borderRadius: 4,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                    title="Opciones"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="1.5" />
                      <circle cx="12" cy="5" r="1.5" />
                      <circle cx="12" cy="19" r="1.5" />
                    </svg>
                  </button>

                  {/* Dropdown */}
                  {menuOpenId === conv.id && (
                    <div
                      className="z-20"
                      style={{
                        position: "absolute",
                        right: 0,
                        top: "100%",
                        marginTop: 4,
                        background: "var(--color-bg-primary)",
                        border: "1px solid var(--color-border)",
                        borderRadius: 8,
                        boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                        padding: "4px",
                        minWidth: 160,
                        display: "flex",
                        flexDirection: "column",
                        gap: 2,
                      }}
                    >
                      <button
                        onClick={(e) => {
                          togglePin(e, conv.id);
                          setMenuOpenId(null);
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.background = "var(--color-bg-secondary)"}
                        onMouseLeave={(e) => e.currentTarget.style.background = "none"}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 8,
                          padding: "8px 10px",
                          fontSize: "0.8125rem",
                          color: "var(--color-text-primary)",
                          background: "none",
                          border: "none",
                          borderRadius: 4,
                          cursor: "pointer",
                          textAlign: "left",
                          transition: "background 0.2s",
                        }}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          {conv.isPinned ? (
                            <>
                              <line x1="12" y1="17" x2="12" y2="22" />
                              <path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 11.24V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3v5.24a2 2 0 0 1-1.11 1.31l-1.78.9A2 2 0 0 0 5 15.24Z" />
                              <line x1="2" y1="2" x2="22" y2="22" />
                            </>
                          ) : (
                            <>
                              <line x1="12" y1="17" x2="12" y2="22" />
                              <path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 11.24V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3v5.24a2 2 0 0 1-1.11 1.31l-1.78.9A2 2 0 0 0 5 15.24Z" />
                            </>
                          )}
                        </svg>
                        {conv.isPinned ? "Desfijar" : "Fijar"}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setRenamingId(conv.id);
                          setRenameValue(conv.title);
                          setMenuOpenId(null);
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.background = "var(--color-bg-secondary)"}
                        onMouseLeave={(e) => e.currentTarget.style.background = "none"}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 8,
                          padding: "8px 10px",
                          fontSize: "0.8125rem",
                          color: "var(--color-text-primary)",
                          background: "none",
                          border: "none",
                          borderRadius: 4,
                          cursor: "pointer",
                          textAlign: "left",
                          transition: "background 0.2s",
                        }}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M12 20h9" />
                          <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
                        </svg>
                        Cambiar nombre
                      </button>
                      <button
                        onClick={(e) => {
                          deleteConv(e, conv.id);
                          setMenuOpenId(null);
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.background = "var(--color-bg-secondary)"}
                        onMouseLeave={(e) => e.currentTarget.style.background = "none"}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 8,
                          padding: "8px 10px",
                          fontSize: "0.8125rem",
                          color: "red",
                          background: "none",
                          border: "none",
                          borderRadius: 4,
                          cursor: "pointer",
                          textAlign: "left",
                          transition: "background 0.2s",
                        }}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="3 6 5 6 21 6" />
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                        </svg>
                        Eliminar
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </nav>
      )}

      {/* Bottom — theme + actions */}
      <div
        className="p-3 flex flex-col gap-2"
        style={{ borderTop: "1px solid var(--color-border)" }}
      >
        {/* Administrar Fichas - Solo si es admin y está logueado */}
        {isLoggedIn && isAdmin && (
          <button
            id="admin-panel-btn"
            onClick={() => window.open("http://localhost:3001", "_blank")}
            className="btn-ghost"
            style={{
              width: "100%",
              justifyContent: collapsed ? "center" : "flex-start",
              gap: collapsed ? 0 : 8,
              padding: "9px 12px",
              fontSize: "0.8125rem",
            }}
            aria-label="Ir al panel de administración"
            title="Administrar Fichas"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="7" rx="1" />
              <rect x="14" y="3" width="7" height="7" rx="1" />
              <rect x="3" y="14" width="7" height="7" rx="1" />
              <rect x="14" y="14" width="7" height="7" rx="1" />
            </svg>
            {!collapsed && "Administrar Fichas"}
          </button>
        )}

        {/* Botón de Iniciar Sesión / Perfil */}
        <button
          id="sidebar-login-btn"
          onClick={() => {
            // Simulamos el inicio de sesión para que puedas ver cómo cambia
            setIsLoggedIn(!isLoggedIn);
          }}
          className={isLoggedIn ? "btn-ghost" : "btn-primary"}
          style={{
            width: "100%",
            justifyContent: collapsed ? "center" : "flex-start",
            gap: collapsed ? 0 : 8,
            padding: "9px 12px",
            fontSize: "0.8125rem",
          }}
          aria-label={isLoggedIn ? "Mi Perfil" : "Iniciar sesión"}
          title={isLoggedIn ? "Mi Perfil" : "Iniciar sesión"}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          {!collapsed && (isLoggedIn ? "Mi Perfil" : "Iniciar sesión")}
        </button>

        <button
          id="chat-theme-toggle"
          onClick={toggleTheme}
          className="btn-ghost"
          style={{
            width: "100%",
            justifyContent: collapsed ? "center" : "flex-start",
            gap: collapsed ? 0 : 8,
            padding: "9px 12px",
            fontSize: "0.8125rem",
          }}
          aria-label="Cambiar tema"
        >
          {isDark ? (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
            </svg>
          ) : (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          )}
          {!collapsed && (isDark ? "Modo claro" : "Modo oscuro")}
        </button>
      </div>
    </aside>
  );
}
