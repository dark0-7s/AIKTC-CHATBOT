import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        homepage: resolve(__dirname, 'homepage-replica.html'),
      },
    },
  },
  server: {
    port: 5175,
    proxy: {
      '/api': 'http://localhost:8001'
    }
  }
})
