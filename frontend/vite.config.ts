import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// El proxy /api evita problemas de CORS en desarrollo apuntando al backend.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
