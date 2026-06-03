/** @type {import('next').NextConfig} */
const rawBackend = process.env.BACKEND_URL || "http://localhost:8001";
const backendUrl = rawBackend.startsWith("http") ? rawBackend : `https://${rawBackend}`;

const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
