import type { NextConfig } from "next";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8001";

const nextConfig: NextConfig = {
  // The floating Next dev badge sat on top of the Home tab in every screenshot.
  devIndicators: false,
  // Media served by the API's local-disk Object Storage stand-in, and the
  // module's own static assets, are proxied so a `<img src="/media/...">`
  // works from either origin without hardcoding the API port in markup.
  async rewrites() {
    return [
      { source: "/media/:path*", destination: `${API_BASE}/media/:path*` },
    ];
  },
};

export default nextConfig;
