import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

vi.mock('@/lib/tenant', () => ({
  ensureTenant: vi.fn(async () => 't1'),
  getTenant: vi.fn(() => 't1'),
}))

// Mock api client to avoid network during render
vi.mock('@/lib/apiClient', () => ({
  indexFiles: vi.fn(),
  getStatus: vi.fn(),
}))

import UploadPage from '@/app/upload/page'

describe('UploadPage (smoke)', () => {
  it('renders heading and button', () => {
    render(<UploadPage />)
    expect(screen.getByText('Загрузка документов')).toBeInTheDocument()
    expect(screen.getByText('Индексировать')).toBeInTheDocument()
  })
})

