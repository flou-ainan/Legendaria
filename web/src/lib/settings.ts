// The editor's settings, from settings.json (basic and advanced); the Settings screen will edit them later.
import raw from './settings.json'

export type PlayheadMode = 'auto' | 'arrow' | 'center'

export const settings = {
  playhead: raw.basic.playhead as PlayheadMode,
  ...raw.advanced,
}
