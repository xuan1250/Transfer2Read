import type { Metadata } from "next";
import "./globals.css";
import { TopBar } from "@/components/layout/TopBar";

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
    <html lang="en">
      <body className="antialiased">
        <TopBar />
        <main>{children}</main>
      </body>
    </html>
  );
}
