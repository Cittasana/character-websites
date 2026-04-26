/**
 * Character website root — redirects to the default mode (cv or dating).
 */

import { redirect, notFound } from "next/navigation";
import { getCharacterPersonalitySchema } from "@/lib/character-data";

interface PageProps {
  params: Promise<{ username: string }>;
  searchParams: Promise<{ mode?: string }>;
}

export default async function CharacterRootPage({
  params,
  searchParams,
}: PageProps) {
  const { username } = await params;
  const { mode } = await searchParams;

  const schema = await getCharacterPersonalitySchema(username);
  if (!schema) notFound();

  const config = schema.website_config;

  // Determine where to redirect
  if (mode === "dating" && (config.mode === "dating" || config.mode === "both")) {
    redirect(`/${username}/dating`);
  }

  if (config.mode === "dating") {
    redirect(`/${username}/dating`);
  }

  // Default to CV
  redirect(`/${username}/cv`);
}
