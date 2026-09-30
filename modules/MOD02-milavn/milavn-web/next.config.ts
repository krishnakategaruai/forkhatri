import type { NextConfig } from "next";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8001";
// Server-side route to the API inside the deployment network; defaults to the public base.
const API_SERVER_BASE = process.env.MILAVN_API_INTERNAL_URL || API_BASE;

// [ForKhatri TR22, deployment kit 2026-09-14] Production serves Milavn as a
// Next.js zone under `/milavn` on the one ForKhatri origin. Every value comes
// from the build environment and is unset in local development, so
// `next dev` on :3001 behaves exactly as before.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH?.replace(/\/+$/, "") || undefined;

const nextConfig: NextConfig = {
  basePath,
  assetPrefix: basePath,
  // Container builds set NEXT_OUTPUT_STANDALONE=1; a separate NEXT_DIST_DIR lets
  // a production build run without touching a running dev server's `.next`.
  output: process.env.NEXT_OUTPUT_STANDALONE === "1" ? "standalone" : undefined,
  distDir: process.env.NEXT_DIST_DIR || ".next",
  poweredByHeader: false,
  // The floating Next dev badge sat on top of the Home tab in every screenshot.
  devIndicators: false,
  // TUNNEL_DEV_ORIGIN is set by `npm run dev:tunnel` (scripts/tunnel.mjs) to
  // that run's actual Cloudflare Quick Tunnel hostname — never hardcoded,
  // since `next dev` otherwise rejects requests whose Host isn't localhost.
  allowedDevOrigins: process.env.TUNNEL_DEV_ORIGIN ? [process.env.TUNNEL_DEV_ORIGIN] : [],
  // Media served by the API's local-disk Object Storage stand-in, and the
  // module's own static assets, are proxied so a `<img src="/media/...">`
  // works from either origin without hardcoding the API port in markup.
  // While tunnelling, identity and this module's own API are proxied the
  // same way for the same reason: two different tunnel hostnames are two
  // different sites, so a session cookie from a direct cross-site call never
  // comes back on the next request — the destination is always plain
  // localhost, since this hop is server-to-server on the same machine.
  async rewrites() {
    return [
      { source: "/media/:path*", destination: `${API_SERVER_BASE}/media/:path*` },
      ...(process.env.TUNNEL_DEV_ORIGIN
        ? [
            { source: "/tunnel-proxy/identity/:path*", destination: "http://localhost:8100/:path*" },
            { source: "/tunnel-proxy/api/:path*", destination: "http://localhost:8001/:path*" },
          ]
        : []),
    ];
  },
};

export default nextConfig;
