/**
 * ISR On-Demand Revalidation Endpoint
 *
 * Called by the backend via webhook when a user's personality schema is updated.
 * Clears the Next.js cache for the user's pages.
 *
 * POST /api/revalidate
 * Body: { username: string, secret: string }
 */

import { NextRequest, NextResponse } from "next/server";
import { revalidatePath } from "next/cache";

interface RevalidateBody {
  username: string;
  secret: string;
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  let body: RevalidateBody;

  try {
    body = (await request.json()) as RevalidateBody;
  } catch {
    return NextResponse.json(
      { error: "Invalid JSON body" },
      { status: 400 },
    );
  }

  const { username, secret } = body;

  if (!username || typeof username !== "string") {
    return NextResponse.json(
      { error: "Missing or invalid username" },
      { status: 400 },
    );
  }

  // Verify secret
  const expectedSecret = process.env.ISR_REVALIDATION_SECRET;
  if (!expectedSecret || secret !== expectedSecret) {
    return NextResponse.json(
      { error: "Invalid revalidation secret" },
      { status: 401 },
    );
  }

  try {
    // Revalidate all pages for this user
    revalidatePath(`/${username}/cv`);
    revalidatePath(`/${username}/dating`);

    return NextResponse.json({
      revalidated: true,
      username,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Revalidation failed";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
