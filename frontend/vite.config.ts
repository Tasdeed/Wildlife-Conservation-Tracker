import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// base must match the GitHub Pages repo subpath so built asset URLs resolve.
// The repo is Tasdeed/Wildlife-Conservation-Tracker, so the capitalisation
// here has to match it exactly -- the served path is case-sensitive.
// https://vite.dev/config/
export default defineConfig({
  base: '/Wildlife-Conservation-Tracker/',
  plugins: [react(), tailwindcss()],
})
