"use client";

import { useState } from "react";

export interface LiteraryCardData {
  respuesta_texto: string;
  metadata: {
    nombre: string;
    disciplina: string;
    periodo: string;
    lugar: string;
    imagen?: string;
    imagenes?: string[];
    audios?: string[];
    pdfs?: string[];
  };
}

interface LiteraryCardProps {
  data: LiteraryCardData;
  isAnimating?: boolean;
}

export function LiteraryCard({ data, isAnimating = false }: LiteraryCardProps) {
  const [audioPlaying, setAudioPlaying] = useState(false);
  const [audioProgress, setAudioProgress] = useState(0);
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [galleryIndex, setGalleryIndex] = useState(0);

  const { metadata } = data;

  const handleAudioToggle = () => {
    setAudioPlaying((p) => !p);
    // Simulamos progreso de audio con mock data
    if (!audioPlaying) {
      const interval = setInterval(() => {
        setAudioProgress((p) => {
          if (p >= 100) {
            clearInterval(interval);
            setAudioPlaying(false);
            return 0;
          }
          return p + 0.5;
        });
      }, 80);
    }
  };

  return (
    <div className={`card overflow-hidden ${isAnimating ? "animate-fade-slide-up" : ""}`}>
      {/* Header de la tarjeta — Foto + info del autor */}
      <div
        className="flex items-center gap-4 p-5"
        style={{ borderBottom: "1px solid var(--color-border)" }}
      >
        {/* Foto / Avatar */}
        <div
          className="relative flex-shrink-0 overflow-hidden"
          style={{
            width: 64,
            height: 64,
            borderRadius: 12,
            background: "var(--color-accent-muted)",
            border: "2px solid var(--color-border)",
          }}
        >
          {metadata.imagen ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={metadata.imagen}
              alt={metadata.nombre}
              className="w-full h-full object-cover"
            />
          ) : (
            <div
              className="w-full h-full flex items-center justify-center font-playfair font-bold"
              style={{ fontSize: 24, color: "var(--color-accent)" }}
            >
              {metadata.nombre.charAt(0)}
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <h3
            className="font-playfair font-bold truncate"
            style={{ fontSize: "1.1rem", color: "var(--color-text-primary)" }}
          >
            {metadata.nombre}
          </h3>
          <p style={{ fontSize: "0.8125rem", color: "var(--color-accent)", fontWeight: 600, marginTop: 2 }}>
            {metadata.disciplina}
          </p>
          <p style={{ fontSize: "0.8125rem", color: "var(--color-text-muted)", marginTop: 1 }}>
            {metadata.periodo} · {metadata.lugar}
          </p>
        </div>

        {/* Badge */}
        <span
          className="flex-shrink-0 text-xs font-semibold px-2 py-1 rounded-full"
          style={{
            background: "var(--color-accent-muted)",
            color: "var(--color-accent)",
            border: "1px solid var(--color-accent)",
            opacity: 0.85,
          }}
        >
          Ficha literaria
        </span>
      </div>

      {/* Cuerpo — Texto de respuesta */}
      <div className="p-5" style={{ lineHeight: 1.7, color: "var(--color-text-primary)", fontSize: "0.9375rem" }}>
        <p>{data.respuesta_texto}</p>
      </div>

      {/* Footer multimedia */}
      {(metadata.audios?.length || metadata.pdfs?.length || metadata.imagenes?.length) && (
        <div
          className="px-5 pb-5 flex flex-col gap-3"
          style={{ borderTop: "1px solid var(--color-border)", paddingTop: 16 }}
        >
          {/* Audio Player */}
          {metadata.audios && metadata.audios.length > 0 && (
            <div
              className="flex items-center gap-3 p-3 rounded-xl"
              style={{ background: "var(--color-bg-secondary)", border: "1px solid var(--color-border)" }}
            >
              <button
                onClick={handleAudioToggle}
                className="flex-shrink-0 flex items-center justify-center rounded-full"
                style={{
                  width: 36,
                  height: 36,
                  background: "var(--color-accent)",
                  color: "#fff",
                  border: "none",
                  cursor: "pointer",
                  transition: "all 0.2s",
                }}
                aria-label={audioPlaying ? "Pausar audio" : "Reproducir voz del autor"}
              >
                {audioPlaying ? (
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                    <rect x="2" y="2" width="4" height="10" rx="1"/>
                    <rect x="8" y="2" width="4" height="10" rx="1"/>
                  </svg>
                ) : (
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                    <path d="M3 2.5l9 4.5-9 4.5V2.5z"/>
                  </svg>
                )}
              </button>

              {/* Waveform visual */}
              <div className="flex-1 flex flex-col gap-1">
                <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", fontWeight: 500 }}>
                  🎵 Voz del autor
                </span>
                <div className="flex items-center gap-1" style={{ height: 20 }}>
                  {Array.from({ length: 28 }).map((_, i) => (
                    <div
                      key={i}
                      style={{
                        width: 2,
                        height: `${Math.random() * 12 + 4}px`,
                        borderRadius: 1,
                        background:
                          (i / 28) * 100 <= audioProgress
                            ? "var(--color-accent)"
                            : "var(--color-border-strong)",
                        transition: "background 0.1s",
                        flexShrink: 0,
                      }}
                    />
                  ))}
                </div>
                {/* Progress bar */}
                <div
                  className="rounded-full overflow-hidden"
                  style={{ height: 3, background: "var(--color-border)" }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: `${audioProgress}%`,
                      background: "var(--color-accent)",
                      borderRadius: 2,
                      transition: "width 0.1s linear",
                    }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Botones PDF e imágenes */}
          <div className="flex gap-2 flex-wrap">
            {metadata.pdfs && metadata.pdfs.length > 0 && (
              <a
                href={metadata.pdfs[0]}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-ghost text-sm"
                style={{ padding: "8px 14px", fontSize: "0.8125rem" }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
                Ver obra en PDF
              </a>
            )}

            {metadata.imagenes && metadata.imagenes.length > 0 && (
              <button
                onClick={() => setGalleryOpen(true)}
                className="btn-ghost text-sm"
                style={{ padding: "8px 14px", fontSize: "0.8125rem" }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2"/>
                  <circle cx="8.5" cy="8.5" r="1.5"/>
                  <polyline points="21 15 16 10 5 21"/>
                </svg>
                Galería ({metadata.imagenes.length} fotos)
              </button>
            )}
          </div>
        </div>
      )}

      {/* Lightbox de galería */}
      {galleryOpen && metadata.imagenes && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ background: "rgba(0,0,0,0.85)" }}
          onClick={() => setGalleryOpen(false)}
        >
          <div
            className="relative rounded-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: 700, width: "90%", background: "var(--color-bg-card)" }}
          >
            {/* Header lightbox */}
            <div className="flex justify-between items-center p-4" style={{ borderBottom: "1px solid var(--color-border)" }}>
              <span className="font-playfair font-bold" style={{ color: "var(--color-text-primary)" }}>
                Galería — {metadata.nombre}
              </span>
              <button
                onClick={() => setGalleryOpen(false)}
                style={{ background: "none", border: "none", cursor: "pointer", color: "var(--color-text-muted)", fontSize: 20 }}
              >
                ✕
              </button>
            </div>

            {/* Imagen principal */}
            <div className="flex justify-center items-center p-4" style={{ minHeight: 300, background: "var(--color-bg-secondary)" }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={metadata.imagenes[galleryIndex]}
                alt={`Foto ${galleryIndex + 1} de ${metadata.nombre}`}
                style={{ maxHeight: 400, maxWidth: "100%", borderRadius: 8, objectFit: "contain" }}
              />
            </div>

            {/* Thumbnails */}
            <div className="flex gap-2 p-4 overflow-x-auto">
              {metadata.imagenes.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setGalleryIndex(idx)}
                  style={{
                    flexShrink: 0,
                    width: 64,
                    height: 64,
                    borderRadius: 8,
                    overflow: "hidden",
                    border: idx === galleryIndex ? "2px solid var(--color-accent)" : "2px solid var(--color-border)",
                    background: "none",
                    cursor: "pointer",
                    padding: 0,
                  }}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={img} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
