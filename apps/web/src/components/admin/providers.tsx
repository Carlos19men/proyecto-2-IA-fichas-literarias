"use client";

import { Toaster } from "@/components/ui/toaster";

export function AdminProviders({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <Toaster />
    </>
  );
}
