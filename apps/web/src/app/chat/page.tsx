"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Sidebar } from "@/components/chat/Sidebar";
import { ChatArea } from "@/components/chat/ChatArea";
import { useConversations, ChatMessage } from "@/lib/conversations";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function ChatInner() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || undefined;
  const [isLoading, setIsLoading] = useState(false);

  const {
    conversations,
    activeConvId,
    activeMessages,
    createConversation,
    addMessage,
    selectConversation,
    newConversation,
    deleteConversation,
    setActiveConvId,
  } = useConversations();

  /**
   * Punto de entrada para enviar un mensaje.
   * Crea la conversación si es la primera vez, luego llama al backend.
   */
  const handleSendMessage = async (text: string, history: ChatMessage[]) => {
    if (isLoading) return;

    // Crear conversación si no hay una activa
    let convId = activeConvId;
    if (!convId) {
      convId = createConversation(text);
      setActiveConvId(convId);
    }

    // Agregar mensaje del usuario
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date(),
    };
    addMessage(convId, userMsg);
    setIsLoading(true);

    try {
      const historyPayload = history.map((m) => ({
        role: m.role,
        content: m.content || "",
      }));

      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text, history: historyPayload }),
      });

      if (!res.ok) {
        throw new Error(`Error del servidor: ${res.status}`);
      }

      const data = await res.json();

      const assistantMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        role: "assistant",
        content: data.metadata ? undefined : data.respuesta_texto,
        literaryCard: data.metadata
          ? { respuesta_texto: data.respuesta_texto, metadata: data.metadata }
          : undefined,
        timestamp: new Date(),
        relatedQuestions: data.relatedQuestions || [],
      };

      addMessage(convId, assistantMsg);
    } catch (error) {
      console.error("[Chat] Error al contactar el backend:", error);

      const isNetworkError =
        error instanceof TypeError && error.message.includes("fetch");

      const errorMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        role: "assistant",
        content: isNetworkError
          ? "No pude conectarme al servidor. Verificá que el backend esté corriendo (uvicorn) y que Docker con Neo4j esté activo."
          : `Ocurrió un error al procesar tu consulta. Intenta de nuevo en un momento.`,
        timestamp: new Date(),
        isError: true,
      };

      addMessage(convId, errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-full" style={{ background: "var(--color-bg-primary)" }}>
      {/* Sidebar (izquierda) */}
      <Sidebar
        conversations={conversations}
        activeConvId={activeConvId}
        onSelectConv={selectConversation}
        onNewConv={newConversation}
        onDeleteConv={deleteConversation}
      />

      {/* Main Chat Area (derecha) */}
      <main className="flex-1 flex flex-col min-w-0" style={{ background: "var(--color-bg-primary)" }}>
        <ChatArea
          key={activeConvId ?? "new"}
          initialQuery={activeConvId ? undefined : initialQuery}
          messages={activeMessages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
      </main>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="h-screen w-full flex items-center justify-center text-text-muted">Cargando LetraScopio...</div>}>
      <ChatInner />
    </Suspense>
  );
}
