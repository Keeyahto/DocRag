import React from 'react'
import { describe, it, expect } from 'vitest'
import { renderHighlighted } from '../lib/highlight'
import { render } from '@testing-library/react'

function toText(nodes: any): string {
  // Render inside a wrapper to extract text
  const { container } = render(<div>{nodes}</div>)
  return container.textContent || ''
}

describe('renderHighlighted', () => {
  it('splits and wraps ranges with mark', () => {
    const snippet = 'hello world example';
    const ranges: [number, number][] = [[6, 11]]; // 'world'
    const nodes = renderHighlighted(snippet, ranges)
    const { container } = render(<div>{nodes}</div>)
    const marks = container.querySelectorAll('mark')
    expect(marks.length).toBe(1)
    expect(marks[0].textContent).toBe('world')
    expect(toText(nodes)).toBe('hello world example')
  })

  it('merges overlapping ranges', () => {
    const snippet = 'abcdef';
    const ranges: [number, number][] = [[1,3],[2,5]]; // -> [1,5]
    const { container } = render(<div>{renderHighlighted(snippet, ranges)}</div>)
    const marks = container.querySelectorAll('mark')
    expect(marks.length).toBe(1)
    expect(marks[0].textContent).toBe('bcde')
  })
})
