import { defineConfig } from "orval";

export default defineConfig({
  dekopen: {
    input: "../backend/openapi.yaml",
    output: {
      target: "./src/api/generated/dekopen.ts",
      schemas: "./src/api/generated/models",
      client: "fetch",
      clean: true,
      formatter: "prettier",
      override: {
        mutator: {
          path: "./src/api/apiMutator.ts",
          name: "apiMutator",
        },
      },
    },
  },
});
