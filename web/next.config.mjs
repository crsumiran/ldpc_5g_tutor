/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    // Tutor requests may spend up to 90 seconds waiting on OpenRouter, with
    // one additional structured-response retry. Next's proxy default is 30s.
    proxyTimeout: 210_000,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
