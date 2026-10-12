import path from 'node:path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { tanstackRouter } from '@tanstack/router-plugin/vite';

// https://vitejs.dev/config
export default defineConfig({
  plugins: [
    tanstackRouter({
      routesDirectory: './src/frontend/routes',
      generatedRouteTree: './src/frontend/routeTree.gen.ts',
    }),
    react({ compiler: true }),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src/frontend'),
    },
  },
});
