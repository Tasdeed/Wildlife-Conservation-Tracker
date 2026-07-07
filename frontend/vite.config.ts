import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// base must match the GitHub Pages repo subpath so built asset URLs resolve.
// https://vite.dev/config/
export default defineConfig({
  base: '/wildlife-conservation-tracker/',
  plugins: [react(), tailwindcss()],
})
