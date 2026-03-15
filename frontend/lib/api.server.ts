/**
 * Server-only API helpers that use direct Supabase queries.
 * This file MUST NOT be imported by client components — it uses next/headers.
 *
 * For client-side data fetching, use the backend REST API via lib/api.ts instead.
 */

import type {
  GetWebsiteDataRPCResponse,
  VoiceClip,
} from "@/types/personality-schema";
import { createServerSupabaseClient } from "./supabase/server";

export { ApiError } from "./api";

/**
 * Fetch full website data for a username via Supabase RPC.
 * Used by subdomain pages instead of the backend /api/retrieve/schema endpoint.
 *
 * Returns the raw RPC shape { user, personality, website_configs }.
 * Callers should map this to their rendering model as needed.
 */
export async function getWebsiteData(
  username: string,
): Promise<GetWebsiteDataRPCResponse | null> {
  const supabase = await createServerSupabaseClient();
  const { data, error } = await supabase.rpc("get_website_data", {
    p_username: username,
  });
  if (error || !data) return null;
  return data as GetWebsiteDataRPCResponse;
}

/**
 * Fetch public voice clips for a user directly from Supabase.
 * Note: signed URLs for private storage still require the backend.
 */
export async function getVoiceClipsFromDB(
  userId: string,
): Promise<VoiceClip[]> {
  const supabase = await createServerSupabaseClient();
  const { data, error } = await supabase
    .from("voice_clips")
    .select("*")
    .eq("user_id", userId)
    .eq("is_public", true)
    .order("display_order");
  if (error || !data) return [];
  return data as VoiceClip[];
}
