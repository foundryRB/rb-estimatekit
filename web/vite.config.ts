import { defineConfig } from 'vite';
import type { ProxyOptions } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// Proxy paths that should go to the backend (not the SPA).
const backendProxy: ProxyOptions = {
  target: 'http://127.0.0.1:8000',
  changeOrigin: true,
};

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    open: true,
    proxy: {
      // All API calls
      '/api': backendProxy,
      // Built Slidev presentations  (/projects/{slug}/slides/…)
      // Uses a regex so it doesn't interfere with React SPA routes
      '^/projects/[^/]+/slides': backendProxy,
    },
  },
});
