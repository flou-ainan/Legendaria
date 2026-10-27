// Kept ranges (the parts of the source that survive the cuts), in source seconds.
// Mirrors engine/legendaria_engine/project.py; the server normalizes again on save.

export type Range = [number, number]

export const MIN_RANGE = 0.01

const round = (t: number) => Math.round(t * 1000) / 1000

/** Sort, clip to [0, duration], merge overlaps, drop empty ranges. */
export function normalize(ranges: Range[], duration: number): Range[] {
  const sorted = ranges
    .map(([a, b]): Range => [Math.max(0, a), Math.min(duration, b)])
    .sort((x, y) => x[0] - y[0])
  const out: Range[] = []
  for (const [a, b] of sorted) {
    if (b - a < MIN_RANGE) continue
    const last = out[out.length - 1]
    if (last && a <= last[1]) last[1] = Math.max(last[1], b)
    else out.push([a, b])
  }
  return out.map(([a, b]) => [round(a), round(b)])
}

/** The kept ranges after cutting out [start, end]; cuts shorter than MIN_RANGE are ignored. */
export function removeRange(keep: Range[], start: number, end: number): Range[] {
  if (end - start < MIN_RANGE) return keep
  const out: Range[] = []
  for (const [a, b] of keep) {
    if (end <= a || start >= b) {
      out.push([a, b])
      continue
    }
    if (start - a >= MIN_RANGE) out.push([a, round(start)])
    if (b - end >= MIN_RANGE) out.push([round(end), b])
  }
  return out
}

/** The removed parts: the gaps between kept ranges. */
export function cutsOf(keep: Range[], duration: number): Range[] {
  const cuts: Range[] = []
  let at = 0
  for (const [a, b] of keep) {
    if (a - at >= MIN_RANGE) cuts.push([at, a])
    at = b
  }
  if (duration - at >= MIN_RANGE) cuts.push([at, duration])
  return cuts
}

/** Undo one cut: keep [start, end] again. */
export function restoreRange(keep: Range[], cut: Range, duration: number): Range[] {
  return normalize([...keep, cut], duration)
}

/** Where playback should jump when it is at `t`: the next kept start, `Infinity` past the end, or null if `t` is kept. */
export function skipTarget(keep: Range[], t: number): number | null {
  for (const [a, b] of keep) {
    if (t < a - 0.001) return a
    if (t < b) return null
  }
  return Infinity
}

/** Length of the edited video. */
export function outputDuration(keep: Range[]): number {
  return round(keep.reduce((sum, [a, b]) => sum + b - a, 0))
}

/** `m:ss.cc` for display. */
export function clock(t: number): string {
  const sign = t < 0 ? '-' : ''
  const cs = Math.round(Math.abs(t) * 100)
  const m = Math.floor(cs / 6000)
  const s = Math.floor((cs % 6000) / 100)
  return `${sign}${m}:${String(s).padStart(2, '0')}.${String(cs % 100).padStart(2, '0')}`
}
