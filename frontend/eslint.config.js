export default [
  {
    ignores: ["dist/**"],
  },
  {
    files: ["**/*.{js,ts,tsx}"],
    ignores: ["src/**/*.d.ts"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        document: "readonly",
      },
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    linterOptions: {
      reportUnusedDisableDirectives: true,
    },
    rules: {
      "no-undef": "error",
      "no-unused-vars": "error",
    },
  },
];
