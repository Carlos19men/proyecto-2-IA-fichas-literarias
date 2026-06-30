"use client";

import { useState, useEffect, useRef } from "react";
import { LiteraryCard, LiteraryCardData } from "@/components/LiteraryCard";
import { MOCK_AUTHORS, SUGGESTED_QUESTIONS } from "@/lib/mock-data";
import { useRouter } from "next/navigation";
import { ProfileMenu } from "@/components/ProfileMenu";

// ─── Demo animation sequence ────────────────────────────────────────────────
const DEMO_STEPS = [
  { type: "user", text: "¿Quién fue Teresa de la Parra?" },
  { type: "card", card: MOCK_AUTHORS[1] },
  { type: "chips", chips: ["¿Cuál es su novela más famosa?", "Feminismo en la literatura venezolana"] },
] as const;

// ─── Feature grid ────────────────────────────────────────────────────────────
const FEATURES = [
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
    ),
    title: "Búsqueda semántica",
    desc: "Preguntá en lenguaje natural. El motor entiende contexto, no solo palabras clave.",
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>
      </svg>
    ),
    title: "Audio y fotografías",
    desc: "Escuchá la voz de los autores y explorá galerías fotográficas históricas integradas.",
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
      </svg>
    ),
    title: "Obras completas en PDF",
    desc: "Accedé directamente a textos digitalizados desde la respuesta del agente.",
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    ),
    title: "Memoria contextual",
    desc: "El agente recuerda el hilo de la conversación para respuestas cada vez más precisas.",
  },
];

// ─── Typewriter hook ─────────────────────────────────────────────────────────
function useTypewriter(text: string, speed = 35, active = true) {
  const [displayed, setDisplayed] = useState("");
  useEffect(() => {
    if (!active) { setDisplayed(text); return; }
    setDisplayed("");
    let i = 0;
    const timer = setInterval(() => {
      i++;
      setDisplayed(text.slice(0, i));
      if (i >= text.length) clearInterval(timer);
    }, speed);
    return () => clearInterval(timer);
  }, [text, speed, active]);
  return displayed;
}

// ─── Demo Preview Component ───────────────────────────────────────────────────
function DemoPreview() {
  const [step, setStep] = useState<"idle" | "user" | "typing" | "card" | "chips">("idle");
  const [cardData, setCardData] = useState<LiteraryCardData | null>(null);
  const [showChips, setShowChips] = useState(false);
  const userText = useTypewriter(
    "¿Quién fue Teresa de la Parra?",
    45,
    step === "user"
  );

  useEffect(() => {
    const t1 = setTimeout(() => setStep("user"), 600);
    const t2 = setTimeout(() => setStep("typing"), 2200);
    const t3 = setTimeout(() => {
      setCardData(MOCK_AUTHORS[1]);
      setStep("card");
    }, 3400);
    const t4 = setTimeout(() => setShowChips(true), 4500);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); clearTimeout(t4); };
  }, []);

  return (
    <div
      className="card overflow-hidden"
      style={{ maxWidth: 560, width: "100%", margin: "0 auto" }}
    >
      {/* Demo header */}
      <div
        className="flex items-center gap-2 px-4 py-3"
        style={{ borderBottom: "1px solid var(--color-border)", background: "var(--color-bg-secondary)" }}
      >
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#FF5F57" }} />
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#FEBC2E" }} />
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#28C840" }} />
        <span style={{ marginLeft: 8, fontSize: "0.75rem", color: "var(--color-text-muted)", fontWeight: 500 }}>
          LetraScopio — Vista previa
        </span>
      </div>

      <div className="p-4 flex flex-col gap-3" style={{ minHeight: 240 }}>
        {/* Burbuja del usuario */}
        {step !== "idle" && (
          <div className="flex justify-end animate-fade-slide-up">
            <div
              className="px-4 py-2 rounded-2xl rounded-tr-sm text-sm"
              style={{
                background: "var(--color-accent)",
                color: "#fff",
                maxWidth: "80%",
                lineHeight: 1.5,
              }}
            >
              {userText}
              {step === "user" && userText.length < "¿Quién fue Teresa de la Parra?".length && (
                <span
                  className="animate-blink"
                  style={{ marginLeft: 2, borderRight: "2px solid white", paddingRight: 1 }}
                />
              )}
            </div>
          </div>
        )}

        {/* Typing indicator */}
        {step === "typing" && (
          <div className="flex items-center gap-2 animate-fade-in">
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
              style={{ background: "var(--color-accent-muted)", color: "var(--color-accent)", border: "1px solid var(--color-border)" }}
            >
              LS
            </div>
            <div
              className="flex items-center gap-1 px-3 py-2 rounded-2xl rounded-tl-sm"
              style={{ background: "var(--color-bg-secondary)", border: "1px solid var(--color-border)" }}
            >
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: "var(--color-text-muted)",
                    animation: `waveBar 0.9s ease-in-out ${i * 0.15}s infinite`,
                  }}
                />
              ))}
            </div>
          </div>
        )}

        {/* Literary Card en la demo */}
        {(step === "card" || step === "chips") && cardData && (
          <div className="animate-fade-slide-up" style={{ maxWidth: "95%" }}>
            <LiteraryCard data={cardData} isAnimating />
          </div>
        )}

        {/* Chips de follow-up */}
        {showChips && (
          <div className="flex flex-wrap gap-2 animate-fade-in">
            <span className="chip">¿Cuál es su novela más famosa?</span>
            <span className="chip">Feminismo en la literatura ven.</span>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main Landing Page ───────────────────────────────────────────────────────
export default function Home() {
  const [query, setQuery] = useState("");
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isAdmin] = useState(true); // Para probar la vista de admin
  const mockUser = isLoggedIn
    ? { name: "Fernando Pérez", subtitle: "Centro educativo", initials: "FP" }
    : null;

  const handleSearch = (q: string) => {
    if (!q.trim()) return;
    router.push(`/chat?q=${encodeURIComponent(q.trim())}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") handleSearch(query);
  };

  return (
    <div className="flex flex-col min-h-screen" style={{ background: "var(--color-bg-primary)" }}>
      {/* ── HEADER ─────────────────────────────────────────────────── */}
      <header
        className="flex items-center justify-between px-6 py-4 sticky top-0 z-40"
        style={{
          borderBottom: "1px solid var(--color-border)",
          background: "var(--color-bg-primary)",
          backdropFilter: "blur(12px)",
        }}
      >
        <div className="flex items-center gap-2">
          <span
            className="font-playfair font-bold"
            style={{ fontSize: "1.5rem", color: "var(--color-accent)", letterSpacing: "-0.03em" }}
          >
            LetraScopio
          </span>
        </div>

        <div className="flex items-center gap-2">
          <ProfileMenu
            user={mockUser}
            isAdmin={isAdmin}
            popoverDirection="below"
            onLogin={() => setIsLoggedIn(true)}
            onLogout={() => setIsLoggedIn(false)}
          />
        </div>
      </header>

      {/* ── HERO ───────────────────────────────────────────────────── */}
      <main className="flex-1">
        <section
          className="flex flex-col items-center justify-center text-center px-6"
          style={{ paddingTop: "clamp(4rem, 10vw, 7rem)", paddingBottom: "clamp(3rem, 8vw, 5rem)" }}
        >
          {/* Decorative pill */}
          <div
            className="inline-flex items-center gap-2 rounded-full px-4 py-1.5 mb-6 animate-fade-slide-up"
            style={{
              background: "var(--color-accent-muted)",
              border: "1px solid var(--color-accent)",
              color: "var(--color-accent)",
              fontSize: "0.8125rem",
              fontWeight: 600,
              animationDelay: "0.1s",
              opacity: 0,
              animationFillMode: "forwards",
            }}
          >
            <span>✦</span>
            <span>Literatura venezolana · IA conversacional</span>
          </div>

          {/* Título principal */}
          <h1
            className="font-playfair animate-fade-slide-up"
            style={{
              fontSize: "clamp(2.25rem, 5vw, 4rem)",
              fontWeight: 700,
              lineHeight: 1.1,
              letterSpacing: "-0.03em",
              maxWidth: 720,
              color: "var(--color-text-primary)",
              animationDelay: "0.2s",
              opacity: 0,
              animationFillMode: "forwards",
            }}
          >
            Explora la literatura
            <br />
            <span style={{ color: "var(--color-accent)" }}>venezolana</span> con IA
          </h1>

          <p
            className="animate-fade-slide-up"
            style={{
              marginTop: "1.25rem",
              fontSize: "clamp(1rem, 2vw, 1.1875rem)",
              color: "var(--color-text-muted)",
              maxWidth: 540,
              lineHeight: 1.65,
              animationDelay: "0.35s",
              opacity: 0,
              animationFillMode: "forwards",
            }}
          >
            Consultá sobre autores, obras y corrientes literarias. El agente responde con fichas
            enriquecidas: texto, imágenes, audio y documentos.
          </p>

          {/* Search bar */}
          <div
            className="animate-fade-slide-up"
            style={{
              marginTop: "2.5rem",
              width: "100%",
              maxWidth: 600,
              animationDelay: "0.5s",
              opacity: 0,
              animationFillMode: "forwards",
            }}
          >
            <div className="relative flex items-center">
              <span
                className="absolute left-4"
                style={{ color: "var(--color-text-muted)" }}
                aria-hidden
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
              </span>
              <input
                ref={inputRef}
                id="hero-search"
                type="text"
                className="input-field"
                style={{ paddingLeft: "2.75rem", paddingRight: "7rem" }}
                placeholder="Preguntame sobre un autor u obra..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                aria-label="Buscar autores u obras literarias"
              />
              <button
                id="hero-search-btn"
                onClick={() => handleSearch(query)}
                className="absolute right-2 btn-primary"
                style={{ padding: "8px 18px", fontSize: "0.875rem" }}
              >
                Explorar
              </button>
            </div>
          </div>

          {/* Chips de sugerencia */}
          <div
            className="flex flex-wrap justify-center gap-2 animate-fade-slide-up"
            style={{
              marginTop: "1.25rem",
              maxWidth: 640,
              animationDelay: "0.65s",
              opacity: 0,
              animationFillMode: "forwards",
            }}
          >
            {SUGGESTED_QUESTIONS.slice(0, 4).map((q) => (
              <button
                key={q}
                id={`chip-${q.replace(/\s+/g, "-").toLowerCase().slice(0, 30)}`}
                className="chip"
                onClick={() => handleSearch(q)}
              >
                {q}
              </button>
            ))}
          </div>
        </section>

        {/* ── DEMO PREVIEW ───────────────────────────────────────────── */}
        <section
          className="px-6"
          style={{ paddingBottom: "clamp(3rem, 8vw, 5rem)" }}
        >
          <div className="flex flex-col items-center gap-6">
            <div
              className="flex items-center gap-3 animate-fade-in"
              style={{ animationDelay: "0.9s", opacity: 0, animationFillMode: "forwards" }}
            >
              <div style={{ height: 1, width: 60, background: "var(--color-border)" }} />
              <span style={{ fontSize: "0.8125rem", color: "var(--color-text-muted)", fontWeight: 500, whiteSpace: "nowrap" }}>
                Así funciona LetraScopio
              </span>
              <div style={{ height: 1, width: 60, background: "var(--color-border)" }} />
            </div>
            <div
              className="animate-fade-slide-up w-full"
              style={{ animationDelay: "1s", opacity: 0, animationFillMode: "forwards" }}
            >
              <DemoPreview />
            </div>
          </div>
        </section>

        {/* ── FEATURE GRID ───────────────────────────────────────────── */}
        <section
          style={{
            background: "var(--color-bg-secondary)",
            borderTop: "1px solid var(--color-border)",
            borderBottom: "1px solid var(--color-border)",
            padding: "clamp(3rem, 8vw, 5rem) 1.5rem",
          }}
        >
          <div style={{ maxWidth: 900, margin: "0 auto" }}>
            <h2
              className="font-playfair text-center"
              style={{
                fontSize: "clamp(1.5rem, 3vw, 2.25rem)",
                fontWeight: 700,
                color: "var(--color-text-primary)",
                marginBottom: "0.75rem",
              }}
            >
              Todo lo que necesitás, en una sola respuesta
            </h2>
            <p
              className="text-center"
              style={{ color: "var(--color-text-muted)", marginBottom: "3rem", maxWidth: 480, margin: "0 auto 3rem" }}
            >
              LetraScopio no devuelve texto plano. Devuelve fichas literarias completas.
            </p>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: "1.5rem",
              }}
            >
              {FEATURES.map((f) => (
                <div
                  key={f.title}
                  className="card"
                  style={{ padding: "1.5rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}
                >
                  <div
                    className="flex items-center justify-center"
                    style={{
                      width: 48,
                      height: 48,
                      borderRadius: 12,
                      background: "var(--color-accent-muted)",
                      color: "var(--color-accent)",
                      border: "1px solid var(--color-border)",
                    }}
                  >
                    {f.icon}
                  </div>
                  <h3
                    className="font-playfair"
                    style={{ fontSize: "1.0625rem", fontWeight: 700, color: "var(--color-text-primary)" }}
                  >
                    {f.title}
                  </h3>
                  <p style={{ fontSize: "0.875rem", color: "var(--color-text-muted)", lineHeight: 1.6 }}>
                    {f.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── CTA ─────────────────────────────────────────────────────── */}
        <section
          className="flex flex-col items-center justify-center text-center px-6"
          style={{ padding: "clamp(3rem, 8vw, 5rem) 1.5rem" }}
        >
          <h2
            className="font-playfair"
            style={{
              fontSize: "clamp(1.5rem, 3vw, 2.25rem)",
              fontWeight: 700,
              color: "var(--color-text-primary)",
              marginBottom: "1rem",
            }}
          >
            ¿Listo para explorar?
          </h2>
          <p style={{ color: "var(--color-text-muted)", marginBottom: "2rem", maxWidth: 400, lineHeight: 1.6 }}>
            Comienza una conversación sobre la literatura venezolana ahora mismo.
          </p>
          <button
            id="cta-start-btn"
            className="btn-primary"
            style={{ fontSize: "1rem", padding: "14px 32px" }}
            onClick={() => router.push("/chat")}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            Abrir el chat
          </button>
        </section>
      </main>

      {/* ── FOOTER ─────────────────────────────────────────────────── */}
      <footer
        style={{
          borderTop: "1px solid var(--color-border)",
          padding: "1.5rem 1.5rem",
          background: "var(--color-bg-secondary)",
        }}
      >
        <div
          className="flex flex-col md:flex-row items-center justify-between gap-3"
          style={{ maxWidth: 900, margin: "0 auto" }}
        >
          <span className="font-playfair font-bold" style={{ color: "var(--color-accent)", fontSize: "1rem" }}>
            LetraScopio
          </span>
          <p style={{ fontSize: "0.8125rem", color: "var(--color-text-muted)", textAlign: "center" }}>
            Proyecto 2 de IA · Literatura venezolana con GraphRAG + LangGraph · PRO-16
          </p>
          <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>
            v0.1.0-beta
          </span>
        </div>
      </footer>
    </div>
  );
}
