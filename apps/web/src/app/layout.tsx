import type { Metadata } from "next";
import { Playfair_Display, Inter } from "next/font/google";
import "./globals.css";

const playfair = Playfair_Display({
  variable: "--font-playfair",
  subsets: ["latin"],
  weight: ["400", "700"],
  display: "swap",
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "LetraScopio — Explora la literatura venezolana con IA",
  description:
    "Agente literario conversacional con memoria y multimedia. Consulta sobre autores, obras y corrientes literarias de Venezuela.",
  keywords: ["literatura venezolana", "IA", "autores", "obras literarias", "LetraScopio"],
  openGraph: {
    title: "LetraScopio",
    description: "Explora la literatura venezolana con inteligencia artificial",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      suppressHydrationWarning
      className={`${playfair.variable} ${inter.variable} h-full`}
    >
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const saved = localStorage.getItem('letrascopio-theme');
                if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                  document.documentElement.classList.add('dark');
                }
              } catch(e) {}
            `,
          }}
        />
      </head>
      <body className="min-h-full flex flex-col font-inter antialiased bg-bg-primary text-text-primary transition-colors duration-300">
        {children}
      </body>
    </html>
  );
}
