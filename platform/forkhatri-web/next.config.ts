import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The floating dev badge covers the command orb in screenshots.
  devIndicators: false,
  poweredByHeader: false,
  // Lets a production build run into a separate folder (NEXT_DIST_DIR=.next-build)
  // without disturbing a running `next dev`, which keeps using `.next`.
  distDir: process.env.NEXT_DIST_DIR || ".next",
  // Container builds set NEXT_OUTPUT_STANDALONE=1 (Dockerfile); local dev and
  // local builds are unchanged. The entrance is the default zone at `/`, so it
  // has no basePath (docs/ParentApp/07-tech-reqs.md TR22).
  output: process.env.NEXT_OUTPUT_STANDALONE === "1" ? "standalone" : undefined,
};

export default nextConfig;
