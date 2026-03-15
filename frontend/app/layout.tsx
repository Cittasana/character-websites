import type { Metadata } from "next";
import "./globals.css";
import { buildFallbackTokens } from "@/lib/tokens";

export const metadata: Metadata = {
  title: "Character Website",
  description: "Your personality-driven personal website",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const fallbackCss = buildFallbackTokens();

  return (
    <html lang="en">
      <head>
        {/* Inject fallback design tokens — character pages override with their own */}
        <style
          id="design-tokens-fallback"
          dangerouslySetInnerHTML={{ __html: fallbackCss }}
        />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
