import { defineConfig } from "vitest/config";

export default defineConfig({
  build: {
    outDir: "dist",
  },
  test: {
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    passWithNoTests: false,
    setupFiles: ["src/test/setup.ts"],
  },
});
