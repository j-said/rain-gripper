import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Будь-який запит, що починається з /api
      '/api': {
        // Перенаправляємо на порт 8000
        target: 'http://localhost:8000',
        changeOrigin: true, // Необхідно для віртуальних хостів
        secure: false,      // Дозволити на http
      },
    },
  },
});