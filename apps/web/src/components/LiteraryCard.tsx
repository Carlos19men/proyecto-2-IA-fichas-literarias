"use client";

import { useState, useRef, useEffect } from "react";

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
  const [audioDuration, setAudioDuration] = useState(0);
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [galleryIndex, setGalleryIndex] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const { metadata } = data;

  // Determinar si hay audios reales (URLs http/https, no mock://)
  const realAudios = (metadata.audios ?? []).filter(
    (url) => url.startsWith("http://") || url.startsWith("https://")
  );

  // Determinar si hay PDFs reales
  const realPdfs = (metadata.pdfs ?? []).filter(
    (url) => url.startsWith("http://") || url.startsWith("https://")
  );

  // Determinar si hay imágenes reales
  const realImagenes = (metadata.imagenes ?? []).filter(
    (url) => url.startsWith("http://") || url.startsWith("https://")
  );

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onTimeUpdate = () => {
      if (audio.duration) {
        setAudioProgress((audio.currentTime / audio.duration) * 100);
      }
    };
    const onLoadedMetadata = () => setAudioDuration(audio.duration);
    const onEnded = () => {
      setAudioPlaying(false);
      setAudioProgress(0);
    };

    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("loadedmetadata", onLoadedMetadata);
    audio.addEventListener("ended", onEnded);

    return () => {
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("loadedmetadata", onLoadedMetadata);
      audio.removeEventListener("ended", onEnded);
    };
  }, []);

  const handleAudioToggle = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (audioPlaying) {
      audio.pause();
    } else {
      audio.play().catch(() => {
        // El browser bloqueó la reproducción o la URL no es accesible
        setAudioPlaying(false);
      });
    }
    setAudioPlaying((p) => !p);
  };

  const formatTime = (seconds: number) => {
    if (!seconds || isNaN(seconds)) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  const hasMultimedia = realAudios.length > 0 || realPdfs.length > 0 || realImagenes.length > 0;

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
          ) : realImagenes.length > 0 ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={realImagenes[0]}
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
            {[metadata.periodo, metadata.lugar].filter(Boolean).join(" · ")}
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

      {/* Footer multimedia — solo si hay archivos reales */}
      {hasMultimedia && (
        <div
          className="px-5 pb-5 flex flex-col gap-3"
          style={{ borderTop: "1px solid var(--color-border)", paddingTop: 16 }}
        >
          {/* Audio Player real */}
          {realAudios.length > 0 && (
            <>
              {/* Elemento audio oculto */}
              <audio ref={audioRef} src={realAudios[0]} preload="metadata" />

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

                {/* Waveform visual + progreso */}
                <div className="flex-1 flex flex-col gap-1">
                  <div className="flex items-center justify-between">
                    <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", fontWeight: 500 }}>
                      🎵 Voz del autor
                    </span>
                    {audioDuration > 0 && (
                      <span style={{ fontSize: "0.6875rem", color: "var(--color-text-muted)" }}>
                        {formatTime((audioProgress / 100) * audioDuration)} / {formatTime(audioDuration)}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1" style={{ height: 20 }}>
                    {Array.from({ length: 28 }).map((_, i) => (
                      <div
                        key={i}
                        style={{
                          width: 2,
                          height: `${(i % 3 === 0 ? 14 : i % 2 === 0 ? 10 : 6)}px`,
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
                  {/* Progress bar clickeable */}
                  <div
                    className="rounded-full overflow-hidden"
                    style={{ height: 3, background: "var(--color-border)", cursor: "pointer" }}
                    onClick={(e) => {
                      const rect = e.currentTarget.getBoundingClientRect();
                      const pct = (e.clientX - rect.left) / rect.width;
                      if (audioRef.current && audioDuration) {
                        audioRef.current.currentTime = pct * audioDuration;
                        setAudioProgress(pct * 100);
                      }
                    }}
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
            </>
          )}

          {/* Botones PDF e imágenes */}
          <div className="flex gap-2 flex-wrap">
            {realPdfs.length > 0 && (
              <a
                href={realPdfs[0]}
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

            {realImagenes.length > 1 && (
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
                Galería ({realImagenes.length} fotos)
              </button>
            )}
          </div>
        </div>
      )}

      {/* Lightbox de galería */}
      {galleryOpen && realImagenes.length > 0 && (
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
                src={realImagenes[galleryIndex]}
                alt={`Foto ${galleryIndex + 1} de ${metadata.nombre}`}
                style={{ maxHeight: 400, maxWidth: "100%", borderRadius: 8, objectFit: "contain" }}
              />
            </div>

            {/* Thumbnails */}
            <div className="flex gap-2 p-4 overflow-x-auto">
              {realImagenes.map((img, idx) => (
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
