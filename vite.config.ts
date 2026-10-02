import { defineConfig, loadEnv } from 'vite'

import { tanstackStart } from '@tanstack/react-start/plugin/vite'

import viteReact from '@vitejs/plugin-react'

const config = defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_")
  return {
    resolve: { tsconfigPaths: true },
    plugins: [tanstackStart(), viteReact()],
    server: {
      host: "127.0.0.1",
      proxy: {
        "/api": {
          target: env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8002",
          changeOrigin: true,
        },
      },
    },
  }
})

export default config
