/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

/**
 * A Codespace serves this app from https://<codespace>-5173.app.github.dev, so
 * the dev server is reached under a hostname it has never heard of and over
 * port 443. Two things break unless they are told:
 *
 *  - Vite refuses an unknown `Host` header since 5.4.12 (allowedHosts). Loopback
 *    and bare IPs are always allowed, so naming the Codespaces suffix is the
 *    whole change, and it costs a local run nothing.
 *  - HMR's websocket derives its port from the dev server (5173), which is not
 *    the port the browser used. Only a Codespace needs the override; locally
 *    the default is already right, and guessing would break plain `vite`.
 */
const codespace = Boolean(process.env.CODESPACE_NAME);

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: [".app.github.dev"],
    ...(codespace ? { host: true, hmr: { clientPort: 443 } } : {}),
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
