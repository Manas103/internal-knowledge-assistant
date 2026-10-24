import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// PORT is read from the environment so a busy default port never has to be cleared.
const port = Number(process.env.PORT) || 5174;

export default defineConfig({
  plugins: [react()],
  server: { port },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/setupTests.ts",
  },
});
