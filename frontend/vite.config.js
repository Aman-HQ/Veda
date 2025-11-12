import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// const CF_HOST = 'probe-tmp-directions-orchestra.trycloudflare.com'  // <--- UPDATE THIS WITH YOUR TUNNEL HOST

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(), 
    tailwindcss(),
  ],
  // server: {
  //   host: true,                       // listen on all interfaces
  //   allowedHosts: [CF_HOST],          // allow Cloudflare tunnel host
  //   hmr: {
  //     host: CF_HOST,                  // HMR over the tunnel
  //     protocol: 'wss',
  //     // port: 443  // <--- THIS IS ONLY FOR PUBLIC HMR, NOT YOUR LOCAL PORT
  //     // IMPORTANT: tell the client to use 443, do NOT bind locally to 443
  //     clientPort: 443
  //   }
  // }
})
