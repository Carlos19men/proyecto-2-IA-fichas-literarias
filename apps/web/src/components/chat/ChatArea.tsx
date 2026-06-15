"use client";

import { useState, useRef, useEffect } from "react";
import { LiteraryCard } from "@/components/LiteraryCard";
import { ChatMessage, getMockResponse, SUGGESTED_QUESTIONS } from "@/lib/mock-data";

interface ChatAreaProps {
  initialQuery?: string;
}

export function ChatArea({ initialQuery }: ChatAreaProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const hasInitialized = useRef(false);

  // Auto-scroll al último mensaje
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Responder query inicial desde la URL
  useEffect(() => {
    if (initialQuery && !hasInitialized.current) {
      hasInitialized.current = true;
      sendMessage(initialQuery);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: text.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    // Simular latencia del backend
    await new Promise((r) => setTimeout(r, 1200 + Math.random() * 800));

    const response = getMockResponse(text);
    setMessages((prev) => [...prev, response]);
    setIsLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize textarea
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
  };

  return (
    <div className="flex flex-col h-full">
      {/* ── Messages area ─────────────────────────────────────────── */}
      <div
        className="flex-1 overflow-y-auto px-4 py-6"
        style={{ maxHeight: "calc(100vh - 140px)" }}
      >
        <div style={{ maxWidth: 720, margin: "0 auto", display: "flex", flexDirection: "column", gap: "1.5rem" }}>

          {/* Empty state */}
          {messages.length === 0 && !isLoading && (
            <div className="flex flex-col items-center justify-center text-center py-16 animate-fade-in">
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 16,
                  background: "var(--color-accent-muted)",
                  border: "1px solid var(--color-border)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  marginBottom: "1rem",
                }}
              >
                <span className="font-playfair font-bold" style={{ fontSize: "1.5rem", color: "var(--color-accent)" }}>
                  LS
                </span>
              </div>
              <h2
                className="font-playfair"
                style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--color-text-primary)", marginBottom: "0.5rem" }}
              >
                ¿Sobre qué querés explorar hoy?
              </h2>
              <p style={{ color: "var(--color-text-muted)", fontSize: "0.9375rem", marginBottom: "1.5rem", maxWidth: 380 }}>
                Preguntame sobre autores, obras, corrientes literarias o épocas de la literatura venezolana.
              </p>
              {/* Suggested chips on empty state */}
              <div className="flex flex-wrap justify-center gap-2" style={{ maxWidth: 480 }}>
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    className="chip"
                    onClick={() => sendMessage(q)}
                    id={`empty-chip-${q.slice(0, 20).replace(/\s+/g, "-").toLowerCase()}`}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          {messages.map((msg) => (
            <div key={msg.id} className="animate-fade-slide-up">
              {msg.role === "user" ? (
                /* User bubble */
                <div className="flex justify-end">
                  <div
                    style={{
                      maxWidth: "75%",
                      padding: "12px 16px",
                      borderRadius: "16px 16px 4px 16px",
                      background: "var(--color-accent)",
                      color: "#fff",
                      fontSize: "0.9375rem",
                      lineHeight: 1.6,
                    }}
                  >
                    {msg.content}
                  </div>
                </div>
              ) : (
                /* Agent response */
                <div className="flex flex-col gap-3">
                  {/* Agent avatar label */}
                  <div className="flex items-center gap-2">
                    <div
                      style={{
                        width: 28,
                        height: 28,
                        borderRadius: 8,
                        background: "var(--color-accent-muted)",
                        border: "1px solid var(--color-border)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      <span className="font-playfair font-bold" style={{ fontSize: "0.625rem", color: "var(--color-accent)" }}>
                        LS
                      </span>
                    </div>
                    <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", fontWeight: 600 }}>
                      LetraScopio
                    </span>
                  </div>

                  {/* Literary card o texto plano */}
                  {msg.literaryCard ? (
                    <LiteraryCard data={msg.literaryCard} isAnimating />
                  ) : (
                    <div
                      style={{
                        maxWidth: "85%",
                        padding: "14px 18px",
                        borderRadius: "4px 16px 16px 16px",
                        background: "var(--color-bg-card)",
                        border: "1px solid var(--color-border)",
                        fontSize: "0.9375rem",
                        lineHeight: 1.7,
                        color: "var(--color-text-primary)",
                      }}
                    >
                      {msg.content}
                    </div>
                  )}

                  {/* Related question chips */}
                  {msg.relatedQuestions && msg.relatedQuestions.length > 0 && (
                    <div className="flex flex-wrap gap-2" style={{ paddingLeft: 0 }}>
                      <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", width: "100%", marginBottom: 2, fontWeight: 500 }}>
                        Preguntas relacionadas:
                      </span>
                      {msg.relatedQuestions.map((q) => (
                        <button
                          key={q}
                          className="chip"
                          onClick={() => sendMessage(q)}
                          id={`related-${q.slice(0, 20).replace(/\s+/g, "-").toLowerCase()}`}
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex flex-col gap-2 animate-fade-in">
              <div className="flex items-center gap-2">
                <div
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: 8,
                    background: "var(--color-accent-muted)",
                    border: "1px solid var(--color-border)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <span className="font-playfair font-bold" style={{ fontSize: "0.625rem", color: "var(--color-accent)" }}>LS</span>
                </div>
                <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", fontWeight: 600 }}>LetraScopio</span>
              </div>
              <div
                className="flex items-center gap-2 px-4 py-3 rounded-2xl"
                style={{
                  background: "var(--color-bg-card)",
                  border: "1px solid var(--color-border)",
                  width: "fit-content",
                }}
              >
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background: "var(--color-accent)",
                      animation: `waveBar 0.9s ease-in-out ${i * 0.15}s infinite`,
                    }}
                  />
                ))}
                <span style={{ fontSize: "0.8125rem", color: "var(--color-text-muted)", marginLeft: 4 }}>
                  Buscando en la biblioteca...
                </span>
              </div>
              {/* Skeleton card */}
              <div className="card p-5 flex flex-col gap-3" style={{ maxWidth: 480 }}>
                <div className="flex items-center gap-3">
                  <div className="skeleton" style={{ width: 56, height: 56, borderRadius: 10 }} />
                  <div className="flex flex-col gap-2 flex-1">
                    <div className="skeleton" style={{ height: 16, borderRadius: 4 }} />
                    <div className="skeleton" style={{ height: 12, width: "60%", borderRadius: 4 }} />
                    <div className="skeleton" style={{ height: 12, width: "40%", borderRadius: 4 }} />
                  </div>
                </div>
                <div className="skeleton" style={{ height: 12, borderRadius: 4 }} />
                <div className="skeleton" style={{ height: 12, borderRadius: 4, width: "85%" }} />
                <div className="skeleton" style={{ height: 12, borderRadius: 4, width: "70%" }} />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* ── Input area ────────────────────────────────────────────── */}
      <div
        className="flex-shrink-0"
        style={{
          borderTop: "1px solid var(--color-border)",
          background: "var(--color-bg-primary)",
          padding: "1rem 1.5rem 1.25rem",
        }}
      >
        <div style={{ maxWidth: 720, margin: "0 auto" }}>
          <div
            className="flex items-end gap-2 rounded-2xl overflow-hidden"
            style={{
              border: "1.5px solid var(--color-border)",
              background: "var(--color-bg-card)",
              boxShadow: "var(--shadow-card)",
              padding: "8px 12px 8px 16px",
              transition: "border-color 0.2s, box-shadow 0.2s",
            }}
            onFocus={() => {}}
          >
            {/* Textarea */}
            <textarea
              ref={inputRef}
              id="chat-input"
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Escribí tu pregunta sobre literatura venezolana..."
              rows={1}
              disabled={isLoading}
              aria-label="Campo de pregunta al agente literario"
              style={{
                flex: 1,
                resize: "none",
                border: "none",
                outline: "none",
                background: "transparent",
                color: "var(--color-text-primary)",
                fontSize: "0.9375rem",
                fontFamily: "var(--font-inter), system-ui, sans-serif",
                lineHeight: 1.6,
                minHeight: 36,
                maxHeight: 160,
                overflow: "auto",
                padding: "4px 0",
              }}
            />

            {/* Mic button */}
            <button
              id="mic-btn"
              onClick={() => setIsRecording((r) => !r)}
              title="Grabar pregunta por voz (próximamente)"
              aria-label="Micrófono para entrada de voz"
              style={{
                flexShrink: 0,
                width: 36,
                height: 36,
                borderRadius: 10,
                background: isRecording ? "var(--color-accent)" : "transparent",
                border: "none",
                cursor: "pointer",
                color: isRecording ? "#fff" : "var(--color-text-muted)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transition: "all 0.2s",
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
            </button>

            {/* Send button */}
            <button
              id="send-btn"
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || isLoading}
              aria-label="Enviar pregunta"
              style={{
                flexShrink: 0,
                width: 36,
                height: 36,
                borderRadius: 10,
                background: input.trim() && !isLoading ? "var(--color-accent)" : "var(--color-bg-secondary)",
                border: "none",
                cursor: input.trim() && !isLoading ? "pointer" : "not-allowed",
                color: input.trim() && !isLoading ? "#fff" : "var(--color-text-muted)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transition: "all 0.2s",
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>

          <p style={{ fontSize: "0.6875rem", color: "var(--color-text-muted)", textAlign: "center", marginTop: "0.5rem" }}>
            Presioná <kbd style={{ padding: "1px 5px", borderRadius: 4, border: "1px solid var(--color-border)", fontSize: "0.6875rem" }}>Enter</kbd> para enviar · <kbd style={{ padding: "1px 5px", borderRadius: 4, border: "1px solid var(--color-border)", fontSize: "0.6875rem" }}>Shift+Enter</kbd> para nueva línea
          </p>
        </div>
      </div>
    </div>
  );
}
