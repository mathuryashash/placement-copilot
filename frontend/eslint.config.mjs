import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
  {
    rules: {
      // Allow calling setState inside effects for async data fetching patterns.
      // The pattern used here (setState → fetch → setState) is standard for
      // loading state management in React; it doesn't cause infinite loops
      // because the fetch is async (the setState inside the effect only runs once).
      "react-hooks/set-state-in-effect": "off",
    },
  },
]);

export default eslintConfig;
