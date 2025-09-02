import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

vi.mock('@/lib/apiClient', () => ({
  ask: vi.fn(async (_tenant: string, _q: string, _k?: number) => ({ answer: 'Ответ', sources: [{ id: '1', score: 1, snippet: 'snip', highlights: [] }] })),
  askStream: vi.fn(async (_tenant: string, _q: string, _k: number|undefined, onContext: any, onToken: any, onDone: any, _onError: any) => {
    onContext([{ id: '1', score: 1, snippet: 'ctx', highlights: [] }]);
    onToken('Hello');
    onToken('!');
    onDone();
  }),
}))

import { AskForm } from '@/components/AskForm'

describe('AskForm', () => {
  it('sends non-stream request and renders answer via callbacks', async () => {
    const onNew = vi.fn()
    const onCtx = vi.fn()
    let text = ''
    render(<AskForm tenant="t1" onNewAnswer={onNew} onContext={onCtx} onText={(t)=>{ text += t }} />)
    const ta = screen.getByPlaceholderText('Ваш вопрос') as HTMLTextAreaElement
    fireEvent.change(ta, { target: { value: 'Что такое DocRAG?' } })
    fireEvent.click(screen.getByText('Спросить (без стрима)'))
    await waitFor(() => expect(onCtx).toHaveBeenCalled())
    expect(text).toContain('Ответ')
  })

  it('streams answer tokens', async () => {
    const onNew = vi.fn()
    const onCtx = vi.fn()
    let text = ''
    render(<AskForm tenant="t1" onNewAnswer={onNew} onContext={onCtx} onText={(t)=>{ text += t }} />)
    const ta = screen.getByPlaceholderText('Ваш вопрос') as HTMLTextAreaElement
    fireEvent.change(ta, { target: { value: 'Стрим?' } })
    fireEvent.click(screen.getByText('Стримить ответ'))
    await waitFor(() => expect(onCtx).toHaveBeenCalled())
    await waitFor(() => expect(text).toBe('Hello!'))
  })
})

