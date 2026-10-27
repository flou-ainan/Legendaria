// The editor's state: the project document, undo history and autosave.
// `$state` makes a value reactive: components that read it update when it changes
// (https://svelte.dev/docs/svelte/$state). The video's current time is NOT kept here
// (ADR-015 player rule); only the index of the cue under the playhead is.
import { previewAss, saveProject, type Cue, type Project, type Suggestion } from './api'
import { removeRange, restoreRange, type Range } from './timeline'

const GROUP_MS = 800 // edits of the same thing within this window undo together (OpenReel pattern)
const SAVE_MS = 400
const HISTORY = 200

class Editor {
  project = $state<Project | null>(null)
  current = $state(-1) // cue under the playhead
  selected = $state(-1) // cue picked on the timeline (shown in the inspector)
  focusText = $state(0) // bumped to focus the inspector's text box
  markIn = $state<number | null>(null) // the range being marked for a cut
  markOut = $state<number | null>(null)
  saveStatus = $state<'saved' | 'saving' | 'error'>('saved')
  saveError = $state('')
  canUndo = $state(false)
  canRedo = $state(false)
  /** Called with fresh `.ass` text after each save, for the live preview. */
  onPreview: (ass: string) => void = () => {}

  private past: string[] = []
  private future: string[] = []
  private lastGroup = ''
  private lastAt = 0
  private timer: ReturnType<typeof setTimeout> | undefined

  load(project: Project | null) {
    this.project = project
    this.selected = -1
    this.markIn = this.markOut = null
    this.past = []
    this.future = []
    this.syncHistory()
  }

  /** Apply `change` to the project as one undoable step; `group` merges rapid edits (typing, dragging). */
  edit(change: (p: Project) => void, group = '') {
    if (!this.project) return
    const now = Date.now()
    if (!group || group !== this.lastGroup || now - this.lastAt > GROUP_MS) {
      this.past.push(JSON.stringify(this.project))
      if (this.past.length > HISTORY) this.past.shift()
    }
    this.lastGroup = group
    this.lastAt = now
    this.future = []
    change(this.project)
    if (this.selected >= this.project.cues.length) this.selected = -1
    this.syncHistory()
    this.scheduleSave()
  }

  undo() {
    this.travel(this.past, this.future)
  }

  redo() {
    this.travel(this.future, this.past)
  }

  private travel(from: string[], to: string[]) {
    const snapshot = from.pop()
    if (!snapshot || !this.project) return
    to.push(JSON.stringify(this.project))
    this.project = JSON.parse(snapshot)
    this.lastGroup = ''
    this.syncHistory()
    this.scheduleSave()
  }

  private syncHistory() {
    this.canUndo = this.past.length > 0
    this.canRedo = this.future.length > 0
  }

  private scheduleSave() {
    this.saveStatus = 'saving'
    clearTimeout(this.timer)
    this.timer = setTimeout(() => this.save(), SAVE_MS)
  }

  private async save() {
    if (!this.project) return
    try {
      // $state.snapshot gives a plain object (no reactive proxy) to send.
      await saveProject($state.snapshot(this.project) as Project)
      this.saveStatus = 'saved'
      this.onPreview(await previewAss())
    } catch (error) {
      this.saveStatus = 'error'
      this.saveError = (error as Error).message
    }
  }

  // --- commands ---------------------------------------------------------------

  setText(i: number, text: string) {
    this.edit((p) => (p.cues[i].text = text), `text:${i}`)
  }

  setTimes(i: number, start: number, end: number) {
    this.edit((p) => {
      const cue = p.cues[i]
      cue.start = Math.max(0, Math.min(start, end))
      cue.end = Math.min(p.duration, Math.max(start, end))
      p.cues.sort((a, b) => a.start - b.start)
      if (this.selected === i) this.selected = p.cues.indexOf(cue) // the block may have moved in the list
    }, `time:${i}`)
  }

  remove(i: number) {
    this.edit((p) => p.cues.splice(i, 1))
  }

  /** Split a cue at time `at` (or its middle), dividing the words or the text. */
  split(i: number, at?: number) {
    this.edit((p) => {
      const cue = p.cues[i]
      const time = at !== undefined && at > cue.start && at < cue.end ? at : (cue.start + cue.end) / 2
      let first: Cue
      let second: Cue
      const words = cue.words ?? []
      const cutAt = words.findIndex((w) => w.start >= time)
      const join = (ws: typeof words) => ws.map((w) => w.word).join('').trim().replace(/\s+/g, ' ')
      // Words are only used while they still spell the cue's text (a manual edit makes them stale).
      if (cutAt > 0 && join(words) === cue.text) {
        first = { start: cue.start, end: time, text: join(words.slice(0, cutAt)), words: words.slice(0, cutAt) }
        second = { start: time, end: cue.end, text: join(words.slice(cutAt)), words: words.slice(cutAt) }
      } else {
        const parts = cue.text.split(' ')
        const half = Math.max(1, Math.ceil(parts.length / 2))
        first = { start: cue.start, end: time, text: parts.slice(0, half).join(' ') }
        second = { start: time, end: cue.end, text: parts.slice(half).join(' ') }
      }
      p.cues.splice(i, 1, first, second)
    })
  }

  /** Apply glossary suggestions as one undo step; each goes to the cue that holds its time and text. */
  applySuggestions(items: Suggestion[]) {
    this.edit((p) => {
      for (const item of items) {
        const cue = p.cues.find((c) => c.start <= item.start + 1e-6 && item.start < c.end && c.text.includes(item.before))
        if (cue) cue.text = cue.text.replace(item.before, () => item.after)
      }
    })
  }

  mergeNext(i: number) {
    this.edit((p) => {
      const [a, b] = [p.cues[i], p.cues[i + 1]]
      if (!b) return
      p.cues.splice(i, 2, {
        start: a.start,
        end: b.end,
        text: `${a.text} ${b.text}`.trim(),
        words: [...(a.words ?? []), ...(b.words ?? [])],
      })
    })
  }

  addAt(t: number) {
    this.edit((p) => {
      p.cues.push({ start: t, end: Math.min(p.duration, t + 1.5), text: '…' })
      p.cues.sort((a, b) => a.start - b.start)
    })
  }

  cut(start: number, end: number) {
    this.edit((p) => (p.keep = removeRange(p.keep, Math.min(start, end), Math.max(start, end))))
  }

  restore(cut: Range) {
    this.edit((p) => (p.keep = restoreRange(p.keep, cut, p.duration)))
  }
}

export const editor = new Editor()
