import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

vi.mock('@/lib/tenant', () => ({
  ensureTenant: vi.fn(async () => 't1'),
  getTenant: vi.fn(() => 't1'),
}))

vi.mock('@/lib/apiClient', () => ({
  ask: vi.fn(),
  askStream: vi.fn(),
}))

import AskPage from '@/app/ask/page'

describe('AskPage (smoke)', () => {
  it('renders heading and controls', () => {
    render(<AskPage />)
    expect(screen.getByText('Задайте вопрос')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Ваш вопрос')).toBeInTheDocument()
  })
})

