import { describe, it, expect, beforeEach } from 'vitest'
import { getTenant, setTenant } from '../lib/tenant'

describe('tenant storage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('saves and loads tenant id', () => {
    expect(getTenant()).toBeNull()
    setTenant('abc')
    expect(getTenant()).toBe('abc')
  })
})

