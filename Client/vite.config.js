import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/cycle-start": "http://localhost:5000",
      "/feed-hold": "http://localhost:5000",
      "/reset": "http://localhost:5000",
      "/coolant": "http://localhost:5000",
      "/emergency": "http://localhost:5000",
      "/optional-stop": "http://localhost:5000",
      "/single-block": "http://localhost:5000",
      "/block-skip": "http://localhost:5000",
      "/health": "http://localhost:5000",
      "/status": "http://localhost:5000",
    },
  },
});
