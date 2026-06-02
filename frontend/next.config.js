/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  rewrites: async () => {
    return {
      fallback: [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*',
        },
      ],
    };
  },
};

module.exports = nextConfig;
