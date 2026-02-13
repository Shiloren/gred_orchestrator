import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    test: {
        // Enable Vitest globals so common testing utilities (and testing-library auto-cleanup)
        // can register hooks without importing them.
        globals: true,
        environment: 'jsdom',
        setupFiles: ['./src/test/setup.ts'],
        include: ['src/**/*.test.{ts,tsx}'],
        coverage: {
            provider: 'v8',
            reporter: ['lcov', 'text'],
            reportsDirectory: './coverage',
            include: ['src/**/*.{ts,tsx}'],
            exclude: [
                'src/main.tsx',
                'src/types.ts',
                'src/test/**',
                'src/**/*.test.{ts,tsx}'
            ]
        }
    }
})
