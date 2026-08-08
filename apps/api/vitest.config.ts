import swc from "unplugin-swc";
import { defineConfig } from "vitest/config";

// swc (not esbuild) so decorator metadata is emitted — required for Nest DI in e2e tests.
export default defineConfig({
  test: {
    include: ["test/**/*.spec.ts"],
  },
  plugins: [
    swc.vite({
      jsc: {
        parser: { syntax: "typescript", decorators: true },
        transform: { legacyDecorator: true, decoratorMetadata: true },
        target: "es2022",
      },
      module: { type: "es6" },
    }),
  ],
});
