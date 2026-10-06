import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
// @ts-expect-error server-only JavaScript plugin
import { developmentApi } from './src/server/dev-api.js'

export default defineConfig(({ mode }) => {
  // loadEnv is server-only here; no credential is inserted into define or JS.
  const env = loadEnv(mode, process.cwd(), '')
  for (const [key, value] of Object.entries(env)) process.env[key] ??= value
  return { plugins: [react(), developmentApi()], server: { host: '127.0.0.1' } }
})
