import "./globals.css";
import type { Metadata } from "next";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";

export const metadata: Metadata = {
  title: "DocRAG",
  description: "Локальный RAG по вашим документам",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body className="min-h-screen flex flex-col">
        <Header />
        <main className="container mx-auto max-w-5xl flex-1 px-4 py-6">{children}</main>
        <Footer />
      </body>
    </html>
  );
}

