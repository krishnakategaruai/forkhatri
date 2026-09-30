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
  // TUNNEL_DEV_ORIGIN is set by `npm run dev:tunnel` (scripts/tunnel.mjs) to
  // that run's actual Cloudflare Quick Tunnel hostname — never hardcoded,
  // since `next dev` otherwise rejects requests whose Host isn't localhost.
  allowedDevOrigins: process.env.TUNNEL_DEV_ORIGIN ? [process.env.TUNNEL_DEV_ORIGIN] : [],
  // While tunnelling, the browser must call identity through THIS app's own
  // origin (/tunnel-proxy/identity/*), not the identity tunnel's separate
  // trycloudflare.com hostname directly — two different tunnel hostnames are
  // two different sites, so a session cookie set by a direct cross-site call
  // never comes back on the next request. The rewrite's destination is always
  // plain localhost: this hop is server-to-server on the same machine and
  // never needs to leave it, tunnelled or not.
  ...(process.env.TUNNEL_DEV_ORIGIN
    ? {
        async rewrites() {
          return [{ source: "/tunnel-proxy/identity/:path*", destination: "http://localhost:8100/:path*" }];
        },
      }
    : {}),
};

export default nextConfig;
