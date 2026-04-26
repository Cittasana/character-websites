/**
 * Character website layout — wraps all character pages.
 *
 * This server component:
 * 1. Fetches the personality schema for the username (Supabase RPC + mapper)
 * 2. Computes design tokens from the schema
 * 3. Injects them as CSS custom properties in <head>
 * 4. Preloads required Google Fonts
 */

import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getCharacterPersonalitySchema } from "@/lib/character-data";
import { buildDesignTokens } from "@/lib/tokens";

interface CharacterLayoutProps {
  children: React.ReactNode;
  params: Promise<{ username: string }>;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ username: string }>;
}): Promise<Metadata> {
  const { username } = await params;

  const schema = await getCharacterPersonalitySchema(username);

  if (!schema) {
    return {
      title: username,
      description: "Character Website",
    };
  }

  return {
    title: schema.full_name,
    description: schema.cv_content.positioning_statement,
    openGraph: {
      title: schema.full_name,
      description: schema.cv_content.positioning_statement,
      type: "profile",
      images: schema.avatar_url ? [{ url: schema.avatar_url }] : [],
    },
  };
}

export default async function CharacterLayout({
  children,
  params,
}: CharacterLayoutProps) {
  const { username } = await params;

  const schema = await getCharacterPersonalitySchema(username);

  if (!schema) {
    notFound();
  }

  const { css: tokenCss, fontUrls } = buildDesignTokens(schema);

  return (
    <>
      {/* Inject persona-specific Google Fonts */}
      {fontUrls.map((url) => (
        <link
          key={url}
          rel="stylesheet"
          href={url}
          crossOrigin="anonymous"
        />
      ))}

      {/* Inject design tokens as CSS custom properties — server-rendered, zero FOUC */}
      <style
        id="design-tokens"
        dangerouslySetInnerHTML={{ __html: tokenCss }}
      />

      {/* Character website content */}
      <div
        className="bg-persona-background"
        style={{ minHeight: "100vh" }}
        data-username={username}
        data-persona={schema.persona_blend.primary}
      >
        {children}
      </div>
    </>
  );
}
