/**
 * Hook de gestión de conversaciones con persistencia en localStorage.
 *
 * Provee el historial real de conversaciones del usuario, sin datos simulados.
 * Cada conversación almacena su id, título (primera pregunta), fecha y mensajes.
 */

"use client";

import { useState, useEffect, useCallback } from "react";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content?: string;
  literaryCard?: {
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
  };
  timestamp: Date;
  relatedQuestions?: string[];
  isError?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  date: string;
  messages: ChatMessage[];
}

const STORAGE_KEY = "letrascopio_conversations";
const MAX_CONVERSATIONS = 50;

function formatDate(date: Date): string {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate());

  if (d.getTime() === today.getTime()) return "Hoy";
  if (d.getTime() === yesterday.getTime()) return "Ayer";

  return date.toLocaleDateString("es-VE", { day: "numeric", month: "short" });
}

function generateId(): string {
  return `conv-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

function truncateTitle(text: string, max = 45): string {
  return text.length > max ? text.slice(0, max).trimEnd() + "…" : text;
}

/** Serializa conversaciones a JSON (convierte Date a string). */
function serialize(convs: Conversation[]): string {
  return JSON.stringify(convs);
}

/** Deserializa conversaciones desde JSON (restaura Date). */
function deserialize(raw: string): Conversation[] {
  try {
    const parsed = JSON.parse(raw) as Conversation[];
    return parsed.map((conv) => ({
      ...conv,
      messages: conv.messages.map((m) => ({
        ...m,
        timestamp: new Date(m.timestamp),
      })),
    }));
  } catch {
    return [];
  }
}

function loadFromStorage(): Conversation[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? deserialize(raw) : [];
  } catch {
    return [];
  }
}

function saveToStorage(convs: Conversation[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, serialize(convs));
  } catch {
    // localStorage lleno o bloqueado — no es crítico
  }
}

// ─── Hook principal ───────────────────────────────────────────────

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);

  // Cargar conversaciones del localStorage al montar
  useEffect(() => {
    const stored = loadFromStorage();
    setConversations(stored);
  }, []);

  /** Mensajes de la conversación activa. */
  const activeMessages: ChatMessage[] =
    conversations.find((c) => c.id === activeConvId)?.messages ?? [];

  /**
   * Crea una nueva conversación con el primer mensaje del usuario.
   * Devuelve el id de la nueva conversación.
   */
  const createConversation = useCallback((firstQuery: string): string => {
    const id = generateId();
    const now = new Date();
    const newConv: Conversation = {
      id,
      title: truncateTitle(firstQuery),
      date: formatDate(now),
      messages: [],
    };
    setConversations((prev) => {
      const updated = [newConv, ...prev].slice(0, MAX_CONVERSATIONS);
      saveToStorage(updated);
      return updated;
    });
    return id;
  }, []);

  /**
   * Agrega un mensaje a la conversación activa.
   */
  const addMessage = useCallback(
    (convId: string, message: ChatMessage) => {
      setConversations((prev) => {
        const updated = prev.map((conv) =>
          conv.id === convId
            ? { ...conv, messages: [...conv.messages, message] }
            : conv
        );
        saveToStorage(updated);
        return updated;
      });
    },
    []
  );

  /**
   * Selecciona una conversación existente del historial.
   */
  const selectConversation = useCallback((id: string) => {
    setActiveConvId(id);
  }, []);

  /**
   * Inicia una nueva conversación vacía (limpiar el chat).
   */
  const newConversation = useCallback(() => {
    setActiveConvId(null);
  }, []);

  /**
   * Elimina una conversación del historial.
   */
  const deleteConversation = useCallback(
    (id: string) => {
      setConversations((prev) => {
        const updated = prev.filter((c) => c.id !== id);
        saveToStorage(updated);
        return updated;
      });
      if (activeConvId === id) {
        setActiveConvId(null);
      }
    },
    [activeConvId]
  );

  return {
    conversations,
    activeConvId,
    activeMessages,
    createConversation,
    addMessage,
    selectConversation,
    newConversation,
    deleteConversation,
    setActiveConvId,
  };
}
