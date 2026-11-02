// Load the bundled font files into the page so the Look menu can show each family in its own face
// (a phone has none of them installed). Done once, the first time the font list opens.
import type { FontEntry } from './api'

const requested = new Set<string>()

export function loadFontFaces(fonts: FontEntry[]) {
  for (const f of fonts) {
    if (requested.has(f.file)) continue
    requested.add(f.file)
    const face = new FontFace(f.family, `url(/api/fonts/${f.file})`)
    face.load().then((loaded) => document.fonts.add(loaded), () => requested.delete(f.file))
  }
}
