import { describe, expect, it } from 'vitest'
import { generatePassword } from './password'

describe('generatePassword', () => {
  it('makes xxxx-xxxx-xxxx from the readable alphabet', () => {
    for (let i = 0; i < 50; i++) expect(generatePassword()).toMatch(/^[a-km-np-z2-9]{4}-[a-km-np-z2-9]{4}-[a-km-np-z2-9]{4}$/)
  })
  it('is not the same twice', () => {
    expect(new Set(Array.from({ length: 30 }, () => generatePassword())).size).toBe(30)
  })
  it('maps bytes to symbols without bias', () => {
    expect(generatePassword(() => new Uint8Array(12))).toBe('aaaa-aaaa-aaaa')
    expect(generatePassword(() => new Uint8Array(12).fill(255))).toBe('9999-9999-9999')
  })
})
