import path from "node:path";

import type { NextConfig } from "next";

// [ForKhatri TR22, deployment kit 2026-09-14] Production serves Mangaly as a
// Next.js zone under `/mangaly` on the one ForKhatri origin. Every value comes
// from the build environment and is unset in local development, so
// `next dev` on :3000 behaves exactly as before.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH?.replace(/\/+$/, "") || undefined;

const nextConfig: NextConfig = {
  // `@forkhatri/chat-core` is shared TypeScript source under the repo's
  // `web/shared/`, not an installed package. Turbopack only resolves imports
  // inside its root, so the root is widened to the repository and the bare
  // specifier is aliased to the source file.
  // `@forkhatri/chat-core` is shared TypeScript source under the repo's
  // `web/shared/`, not an installed package. Turbopack resolves the bare
  // specifier through the tsconfig `paths` entry, but only for files inside
  // its root, so the root is widened from the app to the repository.
  turbopack: {
    root: path.join(__dirname, "..", "..", ".."),
  },
  basePath,
  assetPrefix: basePath,
  // Container builds set NEXT_OUTPUT_STANDALONE=1; a separate NEXT_DIST_DIR lets
  // a production build run without touching a running dev server's `.next`.
  output: process.env.NEXT_OUTPUT_STANDALONE === "1" ? "standalone" : undefined,
  distDir: process.env.NEXT_DIST_DIR || ".next",
  poweredByHeader: false,
  // Development: one signed-in family member per `*.localhost` host, as tabs
  // of one Chrome window (see `resolveApiBase` in lib/api.ts). TUNNEL_DEV_ORIGIN
  // is set by `npm run dev:tunnel` (scripts/tunnel.mjs) to that run's actual
  // Cloudflare Quick Tunnel hostname — never hardcoded, since it's random per run.
  allowedDevOrigins: [
    "*.localhost",
    ...(process.env.TUNNEL_DEV_ORIGIN ? [process.env.TUNNEL_DEV_ORIGIN] : []),
  ],
  // The Next.js dev badge sat on top of the Home tab and the sidebar.
  devIndicators: false,
  // While tunnelling, the browser must call identity and this module's own
  // API through THIS app's own origin, not their separate tunnel hostnames
  // directly — different trycloudflare.com hostnames are different sites, so
  // a session cookie set by a direct cross-site call never comes back on the
  // next request. Destinations are always plain localhost: server-to-server
  // on the same machine, never needing to leave it.
  ...(process.env.TUNNEL_DEV_ORIGIN
    ? {
        async rewrites() {
          return [
            { source: "/tunnel-proxy/identity/:path*", destination: "http://localhost:8100/:path*" },
            { source: "/tunnel-proxy/api/:path*", destination: "http://localhost:8000/:path*" },
          ];
        },
      }
    : {}),
};

export default nextConfig;
