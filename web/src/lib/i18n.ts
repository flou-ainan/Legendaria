// UI strings: English is the source, pt-BR is always maintained (ADR-005).
// To add a language, copy locales/en.json and register it below.
import en from '../locales/en.json'
import ptBR from '../locales/pt-BR.json'

const locales: Record<string, Record<string, string>> = { en, 'pt-BR': ptBR }

/** The interface languages, as `[code, name]` (each name in its own language). */
export const interfaceLanguages: [string, string][] = [['en', 'English'], ['pt-BR', 'Português (Brasil)']]

const KEY = 'legendaria.lang'
const saved = (() => {
  try {
    return localStorage.getItem(KEY)
  } catch {
    return null
  }
})()
export const lang = saved && saved in locales ? saved : navigator.language.toLowerCase().startsWith('pt') ? 'pt-BR' : 'en'

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
