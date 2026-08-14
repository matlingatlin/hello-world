/** @type {import('next').NextConfig} */
module.exports = {
  reactStrictMode: true,
  // pglite is a WASM module and must stay external to the server bundle.
  webpack: (config, { isServer }) => {
    if (isServer) config.externals = [...(config.externals ?? []), "@electric-sql/pglite"];
    return config;
  },
};
