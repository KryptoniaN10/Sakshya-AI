import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/analyze': {
        target: 'http://127.0.0.1:8009',
        changeOrigin: true,
        secure: false
      },
    }
  }
})
