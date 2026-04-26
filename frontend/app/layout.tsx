import type { Metadata } from "next";
import { Inter, Instrument_Serif } from "next/font/google";
import "./globals.css";
import { buildFallbackTokens } from "@/lib/tokens";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const serif = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-serif",
  display: "swap",
});

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
    <html lang="en" className={`${inter.variable} ${serif.variable}`}>
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
