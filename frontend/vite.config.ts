import path from "node:path"
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

// Frontend dev server proxies all /api requests to the FastAPI backend on :8000
// so the React app can use relative URLs (and so MJPEG streaming works without
// CORS quirks).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        // PalmPay + shop marketplace (wallet, cart, checkout) — palmpay backend
        target: process.env.VITE_API_PROXY || "http://127.0.0.1:8001",
        changeOrigin: true,
        ws: true,
      },
    },
  },
  preview: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY || "http://127.0.0.1:8001",
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
