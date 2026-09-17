import type { NextConfig } from "next";

// [ForKhatri TR22, deployment kit 2026-09-14] Production serves Mangaly as a
// Next.js zone under `/mangaly` on the one ForKhatri origin. Every value comes
// from the build environment and is unset in local development, so
// `next dev` on :3000 behaves exactly as before.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH?.replace(/\/+$/, "") || undefined;

const nextConfig: NextConfig = {
  basePath,
  assetPrefix: basePath,
  // Container builds set NEXT_OUTPUT_STANDALONE=1; a separate NEXT_DIST_DIR lets
  // a production build run without touching a running dev server's `.next`.
  output: process.env.NEXT_OUTPUT_STANDALONE === "1" ? "standalone" : undefined,
  distDir: process.env.NEXT_DIST_DIR || ".next",
  poweredByHeader: false,
};

export default nextConfig;
