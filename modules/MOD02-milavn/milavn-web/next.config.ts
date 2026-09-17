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
  // Media served by the API's local-disk Object Storage stand-in, and the
  // module's own static assets, are proxied so a `<img src="/media/...">`
  // works from either origin without hardcoding the API port in markup.
  async rewrites() {
    return [
      { source: "/media/:path*", destination: `${API_SERVER_BASE}/media/:path*` },
    ];
  },
};

export default nextConfig;
