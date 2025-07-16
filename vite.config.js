import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  define: {
    "process.env": {},
    __FINNHUB__: JSON.stringify(process.env.VITE_FINNHUB_KEY),
    __OPENAI__: JSON.stringify(process.env.VITE_OPENAI_KEY),
  },
  build: { outDir: "dist" },
});
