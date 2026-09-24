import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // GitHub Pages serves the site under /Apollo/; Cloudflare Pages at the root
  // (its build sets BASE_PATH=/).
  base: process.env.BASE_PATH || '/Apollo/',
})
