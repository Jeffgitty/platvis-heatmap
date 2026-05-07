import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // GitHub Pages: repo naam als base pad (pas aan na repo aanmaken)
  base: '/platvis-heatmap/',
  server: {
    port: 5173,
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          leaflet: ['leaflet'],
        },
      },
    },
  },
});
