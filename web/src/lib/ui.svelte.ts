// Interface switches that are not part of the project.
export type Panel = 'subtitles' | 'glossary' | 'cuts' | 'export'

/** The page is open through a tunnel or another device: the server's disk is not the user's, so files are uploaded. */
const remote = !['localhost', '127.0.0.1', '[::1]'].includes(location.hostname)

class UI {
  readonly remote = remote
  canBrowse = $state(true) // the server lets this device browse the computer's files (`remote_browse` in access.json)
  snap = $state(true) // the magnet: timeline edges stick to nearby targets
  // The side drawer: the subtitle list is open from the start on wide screens (desktop); on narrow ones it is a bottom sheet, closed.
  panel = $state<Panel | null>(matchMedia('(min-width: 1024px)').matches ? 'subtitles' : null)

  look = $state(false) // the Look menu (a bottom sheet on narrow screens)

  /** A bottom sheet is open: on narrow screens the video then stays in view above it. */
  get sheet() {
    return this.look || this.panel !== null
  }

  toggle(panel: Panel) {
    this.panel = this.panel === panel ? null : panel
  }
}

export const ui = new UI()
