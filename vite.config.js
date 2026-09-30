import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Served at the root (apollorewind.com); BASE_PATH can move it under a path.
  base: process.env.BASE_PATH || '/',
})
