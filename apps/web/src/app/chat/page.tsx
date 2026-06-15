"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Sidebar } from "@/components/chat/Sidebar";
import { ChatArea } from "@/components/chat/ChatArea";

function ChatInner() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || undefined;
  const [activeConvId, setActiveConvId] = useState<string | null>(null);

  const handleNewConv = () => {
    setActiveConvId(null);
    // Podríamos limpiar el initialQuery de la URL si se desea,
    // o forzar una recreación de ChatArea con key={Date.now()}
  };

  return (
    <div className="flex h-screen w-full" style={{ background: "var(--color-bg-primary)" }}>
      {/* Sidebar (izquierda) */}
      <Sidebar
        activeConvId={activeConvId}
        onSelectConv={setActiveConvId}
        onNewConv={handleNewConv}
      />

      {/* Main Chat Area (derecha) */}
      <main className="flex-1 flex flex-col min-w-0" style={{ background: "var(--color-bg-primary)" }}>
        {/* Usamos el key en activeConvId para que se monte un ChatArea nuevo si cambia de conversación (ideal para resetear estados) */}
        <ChatArea
          key={activeConvId ?? "new"}
          initialQuery={activeConvId ? undefined : initialQuery}
        />
      </main>
    </div>
  );
}

export default function ChatPage() {
  return (
    // Es buena práctica envolver en Suspense cuando se usa useSearchParams() en App Router
    <Suspense fallback={<div className="h-screen w-full flex items-center justify-center text-text-muted">Cargando LetraScopio...</div>}>
      <ChatInner />
    </Suspense>
  );
}
