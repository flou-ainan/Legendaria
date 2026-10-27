import { describe, expect, it } from 'vitest'
import { clock, cutsOf, normalize, outputDuration, removeRange, restoreRange, skipTarget, snap, snapPoints } from './timeline'

describe('kept ranges', () => {
  it('normalizes like the engine', () => {
    expect(normalize([[5, 8], [-1, 2], [1.5, 3], [9, 20], [4, 4.001]], 10)).toEqual([[0, 3], [5, 8], [9, 10]])
  })

  it('cuts, lists and restores', () => {
    let keep = removeRange([[0, 10]], 2, 3)
    expect(keep).toEqual([[0, 2], [3, 10]])
    keep = removeRange(keep, 1, 5)
    expect(cutsOf(keep, 10)).toEqual([[1, 5]])
    expect(restoreRange(keep, [1, 5], 10)).toEqual([[0, 10]])
    expect(outputDuration(keep)).toBe(6)
  })

  it('skips cut parts during playback', () => {
    const keep: [number, number][] = [[0, 2], [5, 8]]
    expect(skipTarget(keep, 1)).toBeNull()
    expect(skipTarget(keep, 3)).toBe(5)
    expect(skipTarget(keep, 9)).toBe(Infinity)
  })

  it('random cuts never overlap and stay inside the video', () => {
    let seed = 7
    const rand = () => ((seed = (seed * 16807) % 2147483647) / 2147483647)
    for (let n = 0; n < 200; n++) {
      const duration = 5 + rand() * 55
      let keep: [number, number][] = [[0, duration]]
      for (let i = 0; i < 6; i++) {
        const a = rand() * duration
        keep = removeRange(keep, a, a + rand() * 5)
      }
      const all = [...keep, ...cutsOf(keep, duration)].sort((x, y) => x[0] - y[0])
      let at = 0
      for (const [a, b] of all) {
        expect(Math.abs(a - at)).toBeLessThan(0.002)
        expect(b).toBeGreaterThan(a)
        at = b
      }
      expect(Math.abs(at - duration)).toBeLessThan(0.002)
    }
  })

  it('formats a clock', () => {
    expect(clock(83.456)).toBe('1:23.46')
  })

  it('snaps to the nearest point inside the threshold only', () => {
    const points = snapPoints([5, 1, 3])
    expect(snap(1.04, points, 0.1)).toBe(1)
    expect(snap(2.1, points, 0.1)).toBe(2.1)
    expect(snap(2.95, points, 0.1)).toBe(3)
    expect(snap(4.9, points, 0.2)).toBe(5)
    expect(snap(0.5, [], 0.2)).toBe(0.5)
    expect(snap(9, points, 0.2)).toBe(9)
  })
})
