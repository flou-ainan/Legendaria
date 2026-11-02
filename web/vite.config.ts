import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig } from 'vite'

// The build goes inside the Python package, so `flosub serve` ships it in the wheel.
// `npm run dev` proxies /api to a running `flosub serve VIDEO --no-browser` (port 8765).
const isolation = {
  'Cross-Origin-Opener-Policy': 'same-origin',
  'Cross-Origin-Embedder-Policy': 'require-corp',
}

export default defineConfig({
  plugins: [svelte()],
  server: { headers: isolation, proxy: { '/api': 'http://127.0.0.1:8765' } },
  worker: { format: 'es' },
  optimizeDeps: { exclude: ['jassub'] }, // pre-bundling breaks its worker (spike 1.2)
  build: { target: 'es2022', outDir: '../engine/legendaria_engine/web', emptyOutDir: true },
  test: { include: ['src/**/*.test.ts'] },
})
