// Interface switches that are not part of the project.
export type Panel = 'subtitles' | 'glossary' | 'cuts' | 'export'

/** The page is open through a tunnel or another device: the server's disk is not the user's, so files are uploaded. */
const remote = !['localhost', '127.0.0.1', '[::1]'].includes(location.hostname)

class UI {
  readonly remote = remote
  snap = $state(true) // the magnet: timeline edges stick to nearby targets
  panel = $state<Panel | null>(null) // the side drawer; closed by default (everything happens below the video)

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
