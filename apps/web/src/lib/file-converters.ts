/**
 * Funciones para convertir archivos a texto plano en el cliente.
 * Soporta: .txt, .md (directo), .pdf (extracción básica)
 * Stubs para multimedia: .jpg, .png, .mp3, .mp4
 */

export type SupportedExtension =
  | ".txt"
  | ".md"
  | ".pdf"
  | ".jpg"
  | ".png"
  | ".mp3"
  | ".mp4";

const SUPPORTED_EXTENSIONS: SupportedExtension[] = [
  ".txt",
  ".md",
  ".pdf",
  ".jpg",
  ".png",
  ".mp3",
  ".mp4",
];

export function getExtension(filename: string): string {
  const idx = filename.lastIndexOf(".");
  return idx >= 0 ? filename.slice(idx).toLowerCase() : "";
}

export function isSupported(filename: string): boolean {
  return SUPPORTED_EXTENSIONS.includes(getExtension(filename) as SupportedExtension);
}

export function getSupportedExtensions(): string[] {
  return [...SUPPORTED_EXTENSIONS];
}

export async function fileToText(file: File): Promise<string> {
  const ext = getExtension(file.name) as SupportedExtension;

  switch (ext) {
    case ".txt":
    case ".md":
      return file.text();

    case ".pdf":
      return extractPdfText(file);

    case ".jpg":
    case ".png":
      return `[Imagen: ${file.name} — ${(file.size / 1024).toFixed(1)} KB. Extracción OCR pendiente para PRO-22]`;

    case ".mp3":
      return `[Audio: ${file.name} — ${(file.size / 1024).toFixed(1)} KB. Transcripción pendiente para PRO-22]`;

    case ".mp4":
      return `[Video: ${file.name} — ${(file.size / 1024 / 1024).toFixed(1)} MB. Análisis pendiente para PRO-22]`;

    default:
      throw new Error(`Formato no soportado: ${ext}`);
  }
}

async function extractPdfText(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer();
  const bytes = new Uint8Array(arrayBuffer);

  const textParts: string[] = [];
  const decoder = new TextDecoder("utf-8", { fatal: false });
  const raw = decoder.decode(bytes);

  const streamMatches = raw.match(/stream\n([\s\S]*?)endstream/g);
  if (streamMatches) {
    for (const match of streamMatches) {
      const content = match.replace(/^stream\n/, "").replace(/endstream$/, "");
      const textMatches = content.match(/\(([^)]*)\)/g);
      if (textMatches) {
        for (const t of textMatches) {
          textParts.push(t.slice(1, -1));
        }
      }
    }
  }

  if (textParts.length > 0) {
    return textParts.join(" ");
  }

  const fallback = raw.replace(/[^\x20-\x7E\xC0-\xFF\n]/g, " ").replace(/\s{3,}/g, "\n");
  const lines = fallback.split("\n").filter((l) => l.trim().length > 20);
  if (lines.length > 0) {
    return lines.join("\n");
  }

  return `[PDF: ${file.name} — No se pudo extraer texto. Se requiere OCR para este archivo]`;
}
