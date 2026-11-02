import { describe, expect, it } from 'vitest'

const files = import.meta.glob<Record<string, string>>('../locales/*.json', { eager: true, import: 'default' })
const en = files['../locales/en.json']
const holes = (text: string) => [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort()

describe('locales', () => {
  for (const [path, strings] of Object.entries(files)) {
    const code = path.replace(/^.*\/(.*)\.json$/, '$1')
    it(`${code}: has a name, only known keys and the same {placeholders}`, () => {
      expect(strings._name, 'the "_name" key').toBeTruthy()
      const unknown = Object.keys(strings).filter((key) => !(key in en))
      expect(unknown, 'keys that do not exist in en.json').toEqual([])
      for (const [key, text] of Object.entries(strings)) {
        if (key !== '_name') expect(holes(text), key).toEqual(holes(en[key]))
      }
    })
  }

  it('pt-BR is complete', () => {
    const missing = Object.keys(en).filter((key) => !(key in files['../locales/pt-BR.json']))
    expect(missing).toEqual([])
  })
})
