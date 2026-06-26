"use client";

import { useState, useCallback, useRef } from "react";
import { fileToText, isSupported, getSupportedExtensions } from "@/lib/file-converters";

const MODELOS = [
  { id: "llama3", label: "Llama 3 (8B)" },
  { id: "llama3:70b", label: "Llama 3 (70B)" },
  { id: "qwen2.5:7b", label: "Qwen 2.5 (7B)" },
  { id: "qwen2.5:3b", label: "Qwen 2.5 (3B)" },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FileEntry {
  file: File;
  text: string | null;
  status: "pending" | "converting" | "ready" | "error";
  error?: string;
}

export default function PruebaCargaPage() {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [modelo, setModelo] = useState(MODELOS[0].id);
  const [resultado, setResultado] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const processFiles = useCallback(async (newFiles: File[]) => {
    const valid = newFiles.filter((f) => isSupported(f.name));
    if (valid.length === 0) return;

    const entries: FileEntry[] = valid.map((f) => ({
      file: f,
      text: null,
      status: "converting" as const,
    }));

    setFiles((prev) => [...prev, ...entries]);

    for (let i = 0; i < valid.length; i++) {
      try {
        const text = await fileToText(valid[i]);
        setFiles((prev) =>
          prev.map((entry) =>
            entry.file === valid[i]
              ? { ...entry, text, status: "ready" as const }
              : entry
          )
        );
      } catch (err) {
        setFiles((prev) =>
          prev.map((entry) =>
            entry.file === valid[i]
              ? { ...entry, status: "error" as const, error: String(err) }
              : entry
          )
        );
      }
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const droppedFiles = Array.from(e.dataTransfer.files);
      processFiles(droppedFiles);
    },
    [processFiles]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        processFiles(Array.from(e.target.files));
      }
    },
    [processFiles]
  );

  const handleGenerar = async () => {
    const readyFiles = files.filter((f) => f.status === "ready" && f.text);
    if (readyFiles.length === 0) return;

    const textoCompleto = readyFiles.map((f) => f.text).join("\n\n---\n\n");

    setLoading(true);
    setResultado("");

    try {
      const res = await fetch(`${API_URL}/api/generar-ficha`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto: textoCompleto, modelo }),
      });

      if (!res.ok) {
        const err = await res.text();
        setResultado(JSON.stringify({ error: `HTTP ${res.status}`, detalle: err }, null, 2));
        return;
      }

      const data = await res.json();
      setResultado(JSON.stringify(data, null, 2));
    } catch (err) {
      setResultado(JSON.stringify({ error: "No se pudo conectar con el backend", detalle: String(err) }, null, 2));
    } finally {
      setLoading(false);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearAll = () => {
    setFiles([]);
    setResultado("");
  };

  const readyCount = files.filter((f) => f.status === "ready").length;

  return (
    <div className="min-h-screen bg-bg-primary p-6 md:p-10">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text-primary font-playfair">
              Prueba de Carga
            </h1>
            <p className="text-text-muted text-sm mt-1">
              Sube archivos para generar fichas literarias con IA
            </p>
          </div>
          {/* Selector de modelo */}
          <div className="flex items-center gap-3">
            <label className="text-sm text-text-muted font-medium">Modelo:</label>
            <select
              value={modelo}
              onChange={(e) => setModelo(e.target.value)}
              className="input-field !w-auto !py-2 !px-3 text-sm"
            >
              {MODELOS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>
        </header>

        {/* Drag & Drop Zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`card cursor-pointer border-2 border-dashed p-10 text-center transition-all ${
            dragOver
              ? "border-accent bg-accent-muted scale-[1.01]"
              : "border-border hover:border-accent-light"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            multiple
            accept={getSupportedExtensions().map((e) => e).join(",")}
            onChange={handleFileInput}
            className="hidden"
          />
          <div className="text-4xl mb-3">
            {dragOver ? "📂" : "📄"}
          </div>
          <p className="text-text-primary font-medium">
            {dragOver
              ? "Suelta los archivos aquí"
              : "Arrastra archivos o haz clic para seleccionar"}
          </p>
          <p className="text-text-muted text-sm mt-2">
            Formatos: {getSupportedExtensions().join(", ")}
          </p>
        </div>

        {/* Lista de archivos */}
        {files.length > 0 && (
          <div className="card p-4 space-y-2">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-text-primary">
                {files.length} archivo{files.length > 1 ? "s" : ""} cargado{files.length > 1 ? "s" : ""}
              </span>
              <button onClick={clearAll} className="text-xs text-text-muted hover:text-accent">
                Limpiar todo
              </button>
            </div>
            {files.map((entry, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between py-2 px-3 rounded-lg bg-bg-secondary"
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm">
                    {entry.status === "converting" && "⏳"}
                    {entry.status === "ready" && "✅"}
                    {entry.status === "error" && "❌"}
                  </span>
                  <span className="text-sm text-text-primary truncate max-w-[200px]">
                    {entry.file.name}
                  </span>
                  <span className="text-xs text-text-muted">
                    ({(entry.file.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <button
                  onClick={() => removeFile(idx)}
                  className="text-text-muted hover:text-accent text-sm"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Botón Generar */}
        <button
          onClick={handleGenerar}
          disabled={readyCount === 0 || loading}
          className={`btn-primary w-full justify-center text-base ${
            readyCount === 0 || loading ? "opacity-50 cursor-not-allowed" : ""
          }`}
        >
          {loading ? (
            <>
              <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
              Generando ficha...
            </>
          ) : (
            `Generar Ficha (${readyCount} archivo${readyCount !== 1 ? "s" : ""})`
          )}
        </button>

        {/* Resultado JSON */}
        {resultado && (
          <div className="card p-4 space-y-2">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-text-primary">
                Resultado JSON
              </h2>
              <button
                onClick={() => navigator.clipboard.writeText(resultado)}
                className="text-xs btn-ghost !py-1 !px-2"
              >
                Copiar
              </button>
            </div>
            <pre className="bg-bg-secondary rounded-xl p-4 overflow-x-auto text-xs leading-relaxed text-text-primary max-h-[500px] overflow-y-auto">
              <code>{resultado}</code>
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
