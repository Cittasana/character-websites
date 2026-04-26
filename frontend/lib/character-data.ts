/**
 * Server-only: load public character website schema via Supabase RPC.
 */

import { getWebsiteData } from "@/lib/api.server";
import { mapRpcToPersonalitySchema } from "@/lib/map-rpc-to-personality";
import type { PersonalitySchema } from "@/types/personality-schema";

export async function getCharacterPersonalitySchema(
  username: string,
): Promise<PersonalitySchema | null> {
  const raw = await getWebsiteData(username);
  if (!raw) return null;
  return mapRpcToPersonalitySchema(raw);
}
