import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts", "scripts/**"]),
  {
    // React Compiler heuristics. The fetch-then-setState pattern in the
    // screens is deliberate (reset + load in one callback); keep the signal
    // visible as warnings rather than blocking. `immutability` false-positives
    // on DOM `dataset` mutation in an event handler (theme toggle).
    rules: {
      "react-hooks/set-state-in-effect": "warn",
      "react-hooks/immutability": "warn",
    },
  },
]);

export default eslintConfig;
