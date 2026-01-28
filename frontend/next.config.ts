import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // API rewrites to proxy to FastAPI backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },

  // Image optimization
  images: {
    remotePatterns: [],
  },
};

export default nextConfig;
