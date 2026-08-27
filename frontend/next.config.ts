import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // Broad remote pattern so any poster/backdrop URL an admin adds via
    // Django Admin works, not just TMDB — movies aren't tied to one API (spec section 33).
    remotePatterns: [
      { protocol: 'https', hostname: '**' },
    ],
  },
};

export default nextConfig;
