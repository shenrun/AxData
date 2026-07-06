import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const host = "127.0.0.1";
const port = Number(process.env.AXDATA_WEB_PORT ?? "8667");

export default defineConfig({
  plugins: [react()],
  server: {
    host,
    port
  },
  preview: {
    host,
    port
  }
});
