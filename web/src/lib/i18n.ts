// UI strings: English is the source, pt-BR is always maintained (ADR-005).
// To add a language, copy locales/en.json and register it below.
import en from '../locales/en.json'
import ptBR from '../locales/pt-BR.json'

const locales: Record<string, Record<string, string>> = { en, 'pt-BR': ptBR }

const lang = navigator.language.toLowerCase().startsWith('pt') ? 'pt-BR' : 'en'
const strings = locales[lang]
document.documentElement.lang = lang

/** The translated string for `key`, with `{name}` placeholders filled from `vars`. */
export function t(key: keyof typeof en, vars: Record<string, string | number> = {}): string {
  const text = strings[key] ?? en[key] ?? key
  return text.replace(/\{(\w+)\}/g, (_, name) => String(vars[name] ?? `{${name}}`))
}
