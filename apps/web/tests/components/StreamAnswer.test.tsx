import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { StreamAnswer } from '@/components/StreamAnswer'

describe('StreamAnswer', () => {
  it('renders answer and sources list', () => {
    render(<StreamAnswer answer="Hello" sources={[{ id: '1', score: 0.9, filename: 'a.txt', page: 1, snippet: 'hello world', highlights: [[0,5]] }]} />)
    expect(screen.getByText('Ответ')).toBeInTheDocument()
    expect(screen.getByText(/Источники/)).toBeInTheDocument()
    expect(screen.getByText('a.txt (стр. 1)')).toBeInTheDocument()
  })
})

