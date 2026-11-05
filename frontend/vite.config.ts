import {defineConfig} from 'vite'

// NOTE: @vitejs/plugin-react is not used because the installed Vite 8 (rolldown)
// is incompatible with the available plugin versions in this environment.
// Vite's built-in transform handles .tsx files, so the app builds without it.
export default defineConfig({
  base: '/',
})
