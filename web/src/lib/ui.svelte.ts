// Interface switches that are not part of the project.
export type Panel = 'subtitles' | 'glossary' | 'cuts' | 'export'

class UI {
  snap = $state(true) // the magnet: timeline edges stick to nearby targets
  panel = $state<Panel | null>(null) // the side drawer; closed by default (everything happens below the video)

  toggle(panel: Panel) {
    this.panel = this.panel === panel ? null : panel
  }
}

export const ui = new UI()
