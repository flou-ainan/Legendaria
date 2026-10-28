// A handle on the <video> and the playback commands, shared by components.
// Plain module state, not reactive: the time changes every frame (ADR-015 player rule).
import { editor } from './editor.svelte'
import { skipTarget } from './timeline'

export const player = {
  video: null as HTMLVideoElement | null,

  time(): number {
    return this.video?.currentTime ?? 0
  },

  seek(t: number) {
    if (this.video) this.video.currentTime = Math.max(0, t)
  },

  /** Play or pause; from the end (or inside a cut) playback restarts at the first kept part. */
  togglePlay() {
    const video = this.video
    if (!video || !editor.project) return
    if (!video.paused) return video.pause()
    if (skipTarget(editor.project.keep, video.currentTime) === Infinity) {
      video.currentTime = editor.project.keep[0]?.[0] ?? 0
    }
    void video.play()
  },

  /** Cut out the marked range (I and O) and clear the marks. */
  cut() {
    if (editor.markIn === null || editor.markOut === null) return
    editor.cut(editor.markIn, editor.markOut)
    editor.markIn = editor.markOut = null
  },

  /** Split the cue under the playhead at the playhead. */
  splitAtPlayhead() {
    if (editor.current >= 0) editor.split(editor.current, this.time())
  },
}
