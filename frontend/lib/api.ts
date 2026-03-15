/**
 * Typed API client for all Character-Websites backend endpoints.
 * All functions are async and throw on non-2xx responses.
 */

import type {
  PersonalitySchema,
  VoiceClipsResponse,
  QARequest,
  QAResponse,
  Photo,
} from "@/types/personality-schema";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchJson<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    let message = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) message = body.detail;
    } catch {
      // ignore parse error
    }
    throw new ApiError(res.status, message);
  }

  return res.json() as Promise<T>;
}

// ── Retrieve endpoints ───────────────────────────────────────────────────────

/**
 * Fetch the full personality schema for a given username (subdomain).
 * Backend route: GET /api/retrieve/schema/:username
 */
export async function getPersonalitySchema(
  username: string,
): Promise<PersonalitySchema> {
  return fetchJson<PersonalitySchema>(
    `/api/retrieve/schema/${encodeURIComponent(username)}`,
    {
      next: { revalidate: 3600 },
    } as RequestInit,
  );
}

/**
 * Fetch signed voice clip URLs for a user.
 * Backend route: GET /api/retrieve/voiceclips/:userId
 */
export async function getVoiceClips(
  userId: string,
): Promise<VoiceClipsResponse> {
  return fetchJson<VoiceClipsResponse>(
    `/api/retrieve/voiceclips/${encodeURIComponent(userId)}`,
    {
      cache: "no-store",
    },
  );
}

/**
 * Fetch signed photo URLs for a user.
 * Backend route: GET /api/retrieve/photos/:userId
 */
export async function getPhotos(userId: string): Promise<Photo[]> {
  return fetchJson<Photo[]>(
    `/api/retrieve/photos/${encodeURIComponent(userId)}`,
    {
      cache: "no-store",
    },
  );
}

/**
 * Send a Q&A question and receive a text + optional audio response.
 * Backend route: POST /api/retrieve/qa
 */
export async function sendQA(request: QARequest): Promise<QAResponse> {
  return fetchJson<QAResponse>("/api/retrieve/qa", {
    method: "POST",
    body: JSON.stringify(request),
    cache: "no-store",
  });
}
