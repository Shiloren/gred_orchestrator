import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
            '/ui': 'http://localhost:8000',
            '/tree': 'http://localhost:8000',
            '/file': 'http://localhost:8000',
            '/search': 'http://localhost:8000',
            '/diff': 'http://localhost:8000',
        }
    }
})
