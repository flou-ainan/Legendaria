// A local copy of the work in the browser (IndexedDB), so a crash or a closed tab loses nothing.
// The server also saves the project next to the video; this copy is what survives when that
// save fails or the video moved. It is read only to resume or relink, never as a second source of truth.
import type { Project } from './api'

export type VideoInfo = { path: string; name: string; duration: number; width: number | null; height: number | null }
export type Snapshot = { video: VideoInfo; project: Project; dirty: boolean; savedAt: number }

const DB = 'legendaria'
const STORE = 'kv'
const KEY = 'last'

function open(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB, 1)
    request.onupgradeneeded = () => request.result.createObjectStore(STORE)
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

/** Remember the work in progress. Never throws: a private window may refuse storage. */
export async function remember(snapshot: Snapshot): Promise<void> {
  try {
    const db = await open()
    db.transaction(STORE, 'readwrite').objectStore(STORE).put(snapshot, KEY)
  } catch {
    /* storage unavailable: the server copy still exists */
  }
}

/** The last remembered work, or null. */
export async function lastWork(): Promise<Snapshot | null> {
  try {
    const db = await open()
    return await new Promise((resolve) => {
      const request = db.transaction(STORE).objectStore(STORE).get(KEY)
      request.onsuccess = () => resolve((request.result as Snapshot | undefined) ?? null)
      request.onerror = () => resolve(null)
    })
  } catch {
    return null
  }
}

export async function forget(): Promise<void> {
  try {
    const db = await open()
    db.transaction(STORE, 'readwrite').objectStore(STORE).delete(KEY)
  } catch {
    /* nothing to forget */
  }
}

/** Does `candidate` look like the video the project was made for? Same length (±0.5 s) and screen shape (±1 %). */
export function sameVideo(
  saved: { duration: number; width: number | null; height: number | null },
  candidate: { duration: number; width: number | null; height: number | null },
): { ok: boolean; reason?: 'duration' | 'shape' } {
  if (Math.abs(saved.duration - candidate.duration) > 0.5) return { ok: false, reason: 'duration' }
  if (saved.width && saved.height && candidate.width && candidate.height) {
    const a = saved.width / saved.height
    const b = candidate.width / candidate.height
    if (Math.abs(a - b) / a > 0.01) return { ok: false, reason: 'shape' }
  }
  return { ok: true }
}
