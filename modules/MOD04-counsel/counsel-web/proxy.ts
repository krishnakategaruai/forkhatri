import { NextResponse, type NextRequest } from "next/server";

/**
 * Sign-in handoff from the ForKhatri hub. When the hub and this module sit on
 * unrelated hosts (Cloudflare Quick Tunnels), the hub's cookie cannot reach
 * this host, so the hub sends the member here with a single-use `fk_handoff`
 * code. This proxy redeems it with the identity service server-to-server,
 * copies the returned session cookie onto this host and reloads the same page
 * without the code. Active only when FORKHATRI_IDENTITY_INTERNAL_URL is set
 * (by `npm run dev:tunnel`); otherwise requests pass straight through.
 */
const IDENTITY_INTERNAL_URL = process.env.FORKHATRI_IDENTITY_INTERNAL_URL?.replace(/\/+$/, "");
const HANDOFF_PARAM = "fk_handoff";

export async function proxy(request: NextRequest) {
  const code = request.nextUrl.searchParams.get(HANDOFF_PARAM);
  if (!code || !IDENTITY_INTERNAL_URL) return NextResponse.next();

  // Behind a tunnel this server sees plain http on localhost, so the public
  // scheme and host come from the forwarded headers the tunnel adds.
  const clean = request.nextUrl.clone();
  clean.searchParams.delete(HANDOFF_PARAM);
  const host = request.headers.get("x-forwarded-host") ?? request.headers.get("host");
  if (host) clean.host = host;
  const proto = request.headers.get("x-forwarded-proto");
  if (proto) clean.protocol = `${proto}:`;
  if (request.headers.get("x-forwarded-host") || proto) clean.port = "";
  const response = NextResponse.redirect(clean);
  try {
    const redeemed = await fetch(`${IDENTITY_INTERNAL_URL}/v1/auth/handoff/redeem`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
      cache: "no-store",
    });
    if (redeemed.ok) {
      for (const cookie of redeemed.headers.getSetCookie()) response.headers.append("Set-Cookie", cookie);
    }
  } catch {
    // Identity unreachable: the page's normal sign-in redirect takes over.
  }
  return response;
}

export const config = {
  matcher: ["/((?!_next/|tunnel-proxy/|media/|favicon.ico).*)"],
};
