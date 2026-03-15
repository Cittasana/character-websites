/**
 * Dating Mode page — built fully in Phase 9.
 * Imports and composes all Dating section components.
 */

import { notFound } from "next/navigation";
import { getPersonalitySchema } from "@/lib/api";
import { DatingHero } from "@/components/dating/DatingHero";
import { VoiceClipsGallery } from "@/components/dating/VoiceClipsGallery";
import { PersonalityScores } from "@/components/dating/PersonalityScores";
import { ValuesSection } from "@/components/dating/ValuesSection";
import { PhotoReel } from "@/components/dating/PhotoReel";
import { ModeToggle } from "@/components/shared/ModeToggle";

interface DatingPageProps {
  params: Promise<{ username: string }>;
}

export const revalidate = 3600;

export default async function DatingPage({ params }: DatingPageProps) {
  const { username } = await params;

  let schema;
  try {
    schema = await getPersonalitySchema(username);
  } catch {
    notFound();
  }

  // Access control — if dating mode is disabled, redirect to CV
  if (schema.website_config.mode === "cv") {
    const { redirect } = await import("next/navigation");
    redirect(`/${username}/cv`);
  }

  const showCVToggle =
    schema.website_config.mode === "both" ||
    schema.website_config.mode === "cv";

  return (
    <div className="bg-persona-background" style={{ minHeight: "100vh" }}>
      {showCVToggle && (
        <ModeToggle username={username} currentMode="dating" />
      )}

      <DatingHero schema={schema} />

      {schema.website_config.show_voice_clips && (
        <VoiceClipsGallery userId={schema.user_id} />
      )}

      <PersonalityScores schema={schema} />
      <ValuesSection schema={schema} />

      {schema.website_config.show_photo_reel && (
        <PhotoReel userId={schema.user_id} />
      )}
    </div>
  );
}
