import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    allowedHosts: [".trycloudflare.com"],
    // /reset/ es la página de Django del enlace «Crea tu contraseña»: los correos la arman con
    // la dirección por la que entró el operador o el cliente, que en desarrollo es la de Vite.
    proxy: {
      "/api": { target: "http://127.0.0.1:8080" },
      "/reset": { target: "http://127.0.0.1:8080" },
      "/static": { target: "http://127.0.0.1:8080" },
    },
  },
});
