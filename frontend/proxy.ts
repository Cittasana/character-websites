/**
 * Next.js Proxy — Wildcard Subdomain Routing + Supabase Auth Session Refresh
 *
 * Intercepts every request, extracts the subdomain from the Host header,
 * and rewrites the request to the /{username}/... route so the App Router
 * can serve the correct character website.
 *
 * Also refreshes Supabase auth sessions on every request.
 *
 * Examples:
 *   alex.character.website/          → /alex
 *   alex.character.website/cv        → /alex/cv
 *   alex.character.website/dating    → /alex/dating
 *   character.website/               → / (landing page, no rewrite)
 *   localhost:3000/                  → / (dev: no rewrite)
 *   alex.localhost:3000/             → /alex (dev: subdomain detected)
 */

import { NextRequest, NextResponse } from "next/server";
import { updateSession } from "@/lib/supabase/middleware";

const BASE_DOMAIN = process.env.NEXT_PUBLIC_BASE_DOMAIN ?? "localhost";

/**
 * Extracts the subdomain slug from the Host header.
 * Returns null if the request is for the root domain.
 */
function extractSubdomain(host: string): string | null {
  // Strip port
  const hostname = host.split(":")[0];

  // Pure localhost dev (no subdomain)
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return null;
  }

  // Production: alex.character.website → "alex"
  if (hostname.endsWith(`.${BASE_DOMAIN}`)) {
    const parts = hostname.slice(0, -`.${BASE_DOMAIN}`.length).split(".");
    const subdomain = parts[parts.length - 1];
    if (subdomain && subdomain !== "www") {
      return subdomain;
    }
    return null;
  }

  // Dev subdomain testing: alex.localhost → "alex"
  if (hostname.endsWith(".localhost")) {
    const parts = hostname.split(".");
    if (parts.length >= 2) {
      const subdomain = parts[0];
      if (subdomain && subdomain !== "www") {
        return subdomain;
      }
    }
  }

  return null;
}

export async function proxy(request: NextRequest) {
  // 1. Refresh Supabase auth session
  const sessionResponse = await updateSession(request)

  const host = request.headers.get("host") ?? "";
  const { pathname, search } = request.nextUrl;

  // Skip Next.js internals and static files
  if (
    pathname.startsWith("/_next/") ||
    pathname.startsWith("/api/") ||
    pathname.includes(".")
  ) {
    return sessionResponse;
  }

  const username = extractSubdomain(host);

  if (!username) {
    return sessionResponse;
  }

  // Already prefixed with username? Don't double-rewrite
  if (pathname.startsWith(`/${username}`)) {
    return sessionResponse;
  }

  // Rewrite: /some-path → /username/some-path
  const url = request.nextUrl.clone();
  url.pathname = `/${username}${pathname === "/" ? "" : pathname}`;

  const response = NextResponse.rewrite(url);
  // Copy over any cookies set by Supabase session refresh
  sessionResponse.cookies.getAll().forEach(({ name, value }) => {
    response.cookies.set(name, value);
  });
  response.headers.set("x-username", username);
  response.headers.set("x-original-path", pathname + search);

  return response;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
