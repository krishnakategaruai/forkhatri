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
  // TUNNEL_DEV_ORIGIN is set by `npm run dev:tunnel` (scripts/tunnel.mjs) to
  // that run's actual Cloudflare Quick Tunnel hostname — never hardcoded,
  // since `next dev` otherwise rejects requests whose Host isn't localhost.
  allowedDevOrigins: process.env.TUNNEL_DEV_ORIGIN ? [process.env.TUNNEL_DEV_ORIGIN] : [],
  // While tunnelling, identity and this module's own API are proxied through
  // this app's own origin: two different tunnel hostnames are two different
  // sites, so a session cookie from a direct cross-site call never comes
  // back on the next request. Destination is always plain localhost.
  ...(process.env.TUNNEL_DEV_ORIGIN
    ? {
        async rewrites() {
          return [
            { source: "/tunnel-proxy/identity/:path*", destination: "http://localhost:8100/:path*" },
            { source: "/tunnel-proxy/api/:path*", destination: "http://localhost:8011/:path*" },
          ];
        },
      }
    : {}),
};

export default nextConfig;
