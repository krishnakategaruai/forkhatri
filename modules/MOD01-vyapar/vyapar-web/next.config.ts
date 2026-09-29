import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // [FE2, coordinator] the dev "N" indicator floated over page content in
  // phone screenshots; the dev overlay for errors still works without it.
  devIndicators: false,
  // [FE2] Next 16 holds a lockfile inside the build directory, so a second
  // `next dev` on the same project (a private checker next to the owner's
  // server on 3011) needs its own directory. Unset = the default ".next".
  // It must stay inside the project (see the distDir docs).
  ...(process.env.VYAPAR_WEB_DIST_DIR ? { distDir: process.env.VYAPAR_WEB_DIST_DIR } : {}),
};

export default nextConfig;
