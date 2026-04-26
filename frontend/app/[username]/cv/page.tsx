/**
 * CV Mode page — built fully in Phase 8.
 * Imports and composes all CV section components.
 */

import { notFound } from "next/navigation";
import { getCharacterPersonalitySchema } from "@/lib/character-data";
import { CVHero } from "@/components/cv/CVHero";
import { PersonalityInsights } from "@/components/cv/PersonalityInsights";
import { ExperienceSection } from "@/components/cv/ExperienceSection";
import { CalendarWidget } from "@/components/cv/CalendarWidget";
import { VoiceQA } from "@/components/cv/VoiceQA";
import { ModeToggle } from "@/components/shared/ModeToggle";

interface CVPageProps {
  params: Promise<{ username: string }>;
  searchParams: Promise<{ mode?: string }>;
}

export const revalidate = 3600; // ISR: revalidate every hour

export default async function CVPage({ params }: CVPageProps) {
  const { username } = await params;

  const schema = await getCharacterPersonalitySchema(username);
  if (!schema) notFound();

  const showDatingToggle =
    schema.website_config.mode === "both" ||
    schema.website_config.mode === "dating";

  return (
    <div className="bg-persona-background" style={{ minHeight: "100vh" }}>
      {showDatingToggle && (
        <ModeToggle username={username} currentMode="cv" />
      )}

      <CVHero schema={schema} />
      <PersonalityInsights schema={schema} />
      <ExperienceSection schema={schema} />

      {schema.website_config.calendly_url && (
        <CalendarWidget calendlyUrl={schema.website_config.calendly_url} />
      )}

      <VoiceQA userId={schema.user_id} mode="cv" username={username} />
    </div>
  );
}
