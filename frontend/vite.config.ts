import { defineConfig } from "vitest/config";
import { fieldWorker } from "./scripts/fieldWorker";

export default defineConfig({
  plugins: [fieldWorker()],
  build: {
    outDir: "dist",
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            { name: "telemetry-vendor", test: /node_modules[\\/]posthog-js/ },
            { name: "pdfjs-vendor", test: /node_modules[\\/]pdfjs-dist/ },
          ],
        },
      },
    },
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.DEKOPEN_DEV_API ?? "http://127.0.0.1:8000",
        // The Django dev server closes idle keep-alive sockets without notice;
        // reusing one leaves the proxied request hanging forever. Fresh socket
        // per request + bounded socket timeouts eliminate that stall class.
        timeout: 30_000,
        proxyTimeout: 30_000,
        headers: { connection: "close" },
      },
    },
  },
  test: {
    environment: "jsdom",
    include: [
      "src/**/*.test.ts",
      "src/**/*.test.tsx",
      "scripts/**/*.test.ts",
      "tests/contracts/**/*.test.ts",
    ],
    passWithNoTests: false,
    setupFiles: ["src/test/setup.ts"],
  },
});
