import '@testing-library/jest-dom/vitest'
import { vi } from 'vitest'

// Mock globalThis.location for API_BASE
Object.defineProperty(globalThis, 'location', {
    value: {
        hostname: 'localhost'
    },
    writable: true
})

// Mock fetch globally
globalThis.fetch = vi.fn()

// Mock URL.createObjectURL and revokeObjectURL for export tests
globalThis.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
globalThis.URL.revokeObjectURL = vi.fn()
