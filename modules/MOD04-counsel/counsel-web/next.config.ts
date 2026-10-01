import type { NextConfig } from "next";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8014";
// Server-side hop to the API while tunnelling (set by scripts/tunnel.mjs); the public base otherwise.
const API_SERVER_BASE = process.env.COUNSEL_API_INTERNAL_URL || API_BASE;

const nextConfig: NextConfig = {
  poweredByHeader: false,
  devIndicators: false,
  allowedDevOrigins: process.env.TUNNEL_DEV_ORIGIN ? [process.env.TUNNEL_DEV_ORIGIN] : [],
  async rewrites() {
    return process.env.TUNNEL_DEV_ORIGIN
      ? [
          { source: "/tunnel-proxy/identity/:path*", destination: "http://localhost:8100/:path*" },
          { source: "/tunnel-proxy/api/:path*", destination: `${API_SERVER_BASE}/:path*` },
        ]
      : [];
  },
};

export default nextConfig;
