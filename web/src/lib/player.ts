// A handle on the <video>, shared by components that need to seek or read the time.
// Plain module state, not reactive: the time changes every frame (ADR-015 player rule).

export const player = {
  video: null as HTMLVideoElement | null,

  time(): number {
    return this.video?.currentTime ?? 0
  },

  seek(t: number) {
    if (this.video) this.video.currentTime = Math.max(0, t)
  },
}
