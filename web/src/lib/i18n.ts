// UI strings: English is the source, pt-BR is always maintained (ADR-005).
// Every language is one file in `locales/`, found automatically: see locales/README.md.
import en from '../locales/en.json'

const files = import.meta.glob<Record<string, string>>('../locales/*.json', { eager: true, import: 'default' })
const locales: Record<string, Record<string, string>> = Object.fromEntries(
  Object.entries(files).map(([path, strings]) => [path.replace(/^.*\/(.*)\.json$/, '$1'), strings]),
)

/** The interface languages, as `[code, name]` (each name in its own language, from the file's `_name`). */
export const interfaceLanguages: [string, string][] = Object.entries(locales)
  .map(([code, strings]): [string, string] => [code, strings._name ?? code])
  .sort((a, b) => (a[0] === 'en' ? -1 : b[0] === 'en' ? 1 : a[1].localeCompare(b[1])))

const KEY = 'legendaria.lang'
const saved = (() => {
  try {
    return localStorage.getItem(KEY)
  } catch {
    return null
  }
})()
const browser = navigator.language.toLowerCase()
const guess = Object.keys(locales).find((code) => code.toLowerCase() === browser) ?? Object.keys(locales).find((code) => code.toLowerCase().split('-')[0] === browser.split('-')[0]) ?? 'en'
export const lang = saved && saved in locales ? saved : guess

/** Switch the interface language (remembered; the page reloads so every string updates). */
export function setLang(code: string) {
  try {
    localStorage.setItem(KEY, code)
  } catch {
    /* not remembered: the browser language is used next time */
  }
  location.reload()
}

const strings = locales[lang]
document.documentElement.lang = lang

/** The translated string for `key`, with `{name}` placeholders filled from `vars`. */
export function t(key: keyof typeof en, vars: Record<string, string | number> = {}): string {
  const text = strings[key] ?? en[key] ?? key
  return text.replace(/\{(\w+)\}/g, (_, name) => String(vars[name] ?? `{${name}}`))
}
