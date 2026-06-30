"use client";

import { useState } from "react";
import { useTheme } from "@/lib/theme";
import { Conversation } from "@/lib/conversations";
import { useRouter } from "next/navigation";

interface SidebarProps {
  conversations: Conversation[];
  activeConvId: string | null;
  onSelectConv: (id: string) => void;
  onNewConv: () => void;
  onDeleteConv: (id: string) => void;
}

export function Sidebar({
  conversations,
  activeConvId,
  onSelectConv,
  onNewConv,
  onDeleteConv,
}: SidebarProps) {
  const { isDark, toggleTheme } = useTheme();
  const [collapsed, setCollapsed] = useState(false);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const router = useRouter();

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
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
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
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          {!collapsed && "Nueva conversación"}
        </button>
      </div>

      {/* Conversation list */}
      {!collapsed && (
        <nav className="flex-1 overflow-y-auto p-3 flex flex-col gap-1">
          {conversations.length === 0 ? (
            <p style={{
              fontSize: "0.8125rem",
              color: "var(--color-text-muted)",
              textAlign: "center",
              padding: "2rem 1rem",
              lineHeight: 1.6,
            }}>
              Tus conversaciones aparecerán aquí
            </p>
          ) : (
            <>
              <p style={{
                fontSize: "0.6875rem",
                fontWeight: 700,
                color: "var(--color-text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                padding: "4px 8px 8px",
              }}>
                Historial
              </p>
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  style={{ position: "relative" }}
                  onMouseEnter={() => setHoveredId(conv.id)}
                  onMouseLeave={() => setHoveredId(null)}
                >
                  <button
                    id={`conv-${conv.id}`}
                    onClick={() => onSelectConv(conv.id)}
                    style={{
                      width: "100%",
                      textAlign: "left",
                      padding: "10px 36px 10px 12px",
                      borderRadius: 10,
                      background: activeConvId === conv.id ? "var(--color-accent-muted)" : "transparent",
                      border: activeConvId === conv.id ? "1px solid var(--color-border)" : "1px solid transparent",
                      color: activeConvId === conv.id ? "var(--color-accent)" : "var(--color-text-primary)",
                      cursor: "pointer",
                      transition: "all 0.15s",
                      display: "flex",
                      flexDirection: "column",
                      gap: 2,
                    }}
                  >
                    <span style={{ fontSize: "0.875rem", fontWeight: 500, display: "flex", alignItems: "center", gap: 6 }}>
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, opacity: 0.6 }}>
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                      </svg>
                      <span className="truncate" style={{ maxWidth: 150 }}>{conv.title}</span>
                    </span>
                    <span style={{ fontSize: "0.6875rem", color: "var(--color-text-muted)", paddingLeft: 18 }}>{conv.date}</span>
                  </button>

                  {/* Botón eliminar (aparece en hover) */}
                  {hoveredId === conv.id && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteConv(conv.id);
                      }}
                      title="Eliminar conversación"
                      aria-label="Eliminar conversación"
                      style={{
                        position: "absolute",
                        right: 8,
                        top: "50%",
                        transform: "translateY(-50%)",
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        color: "var(--color-text-muted)",
                        padding: 4,
                        borderRadius: 6,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        transition: "color 0.15s",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = "#ef4444")}
                      onMouseLeave={(e) => (e.currentTarget.style.color = "var(--color-text-muted)")}
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                        <path d="M10 11v6"/>
                        <path d="M14 11v6"/>
                        <path d="M9 6V4h6v2"/>
                      </svg>
                    </button>
                  )}
                </div>
              ))}
            </>
          )}
        </nav>
      )}

      {/* Bottom — theme + actions */}
      <div
        className="p-3 flex flex-col gap-2"
        style={{ borderTop: "1px solid var(--color-border)" }}
      >
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
              <circle cx="12" cy="12" r="5"/>
              <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
            </svg>
          ) : (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          )}
          {!collapsed && (isDark ? "Modo claro" : "Modo oscuro")}
        </button>
      </div>
    </aside>
  );
}
