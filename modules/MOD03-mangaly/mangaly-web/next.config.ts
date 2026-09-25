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
  // of one Chrome window (see `resolveApiBase` in lib/api.ts).
  allowedDevOrigins: ["*.localhost"],
  // The Next.js dev badge sat on top of the Home tab and the sidebar.
  devIndicators: false,
};

export default nextConfig;
