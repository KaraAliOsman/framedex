import { defineConfig } from "vitest/config";

export default defineConfig({
  build: {
    outDir: "dist",
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.ts", "src/**/*.test.tsx", "tests/contracts/**/*.test.ts"],
    passWithNoTests: false,
    setupFiles: ["src/test/setup.ts"],
  },
});
