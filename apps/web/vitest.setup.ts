import '@testing-library/jest-dom'
import React from 'react'
import { vi } from 'vitest'

// Mock next/link to a simple anchor for tests
vi.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children, ...rest }: any) => React.createElement('a', { href, ...rest }, children),
}))

