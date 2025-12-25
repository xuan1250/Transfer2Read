import type { Metadata } from "next";
import "./globals.css";
import { TopBar } from "@/components/layout/TopBar";
import { QueryProvider } from "@/providers/QueryProvider";
import { LimitModalProvider } from "@/contexts/LimitModalContext";
import { Toaster } from "@/components/ui/toaster";

export const metadata: Metadata = {
  title: "Transfer2Read - PDF to EPUB Converter",
  description: "Convert complex PDFs to beautiful EPUBs with AI-powered layout analysis",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased" suppressHydrationWarning>
        <QueryProvider>
          <LimitModalProvider>
            <TopBar />
            <main>{children}</main>
            <Toaster />
          </LimitModalProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
