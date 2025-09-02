import { describe, it, expect } from 'vitest'
import { parseSSE } from '../lib/sse'

function makeStream(chunks: string[]): ReadableStream<Uint8Array> {
  const enc = new TextEncoder()
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const ch of chunks) controller.enqueue(enc.encode(ch))
      controller.close()
    }
  })
}

describe('parseSSE', () => {
  it('parses context, tokens and done', async () => {
    const events: string[] = []
    const stream = makeStream([
      'event: context\n',
      'data: {"sources":[{"id":"1","score":1,"snippet":"a","highlights":[]}]}\n\n',
      'event: token\n',
      'data: {"t":"Hello"}\n\n',
      'event: token\n',
      'data: {"t":"!"}\n\n',
      'event: done\n',
      'data: {"finish_reason":"stop"}\n\n',
    ])
    let tokens = ''
    await parseSSE(stream, {
      onContext: (s) => { events.push('context'); expect(Array.isArray(s)).toBe(true) },
      onToken: (t) => { tokens += t },
      onDone: () => { events.push('done') },
      onError: (m) => { throw new Error(m) },
    })
    expect(tokens).toBe('Hello!')
    expect(events).toEqual(['context','done'])
  })

  it('parses error event', async () => {
    let err = ''
    const stream = makeStream([
      'event: error\n',
      'data: {"message":"oops"}\n\n',
    ])
    await parseSSE(stream, {
      onError: (m) => { err = m }
    })
    expect(err).toBe('oops')
  })
})

