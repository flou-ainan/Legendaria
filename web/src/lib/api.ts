// Talks to `flosub serve` (engine/legendaria_engine/server.py).
import type { Range } from './timeline'

export type Word = { start: number; end: number; word: string; probability?: number }
export type Cue = { start: number; end: number; text: string; words?: Word[] }

/** The project file, `<video>.legendaria.json` (ADR-016). All times in source seconds. */
export type Project = {
  format: 'legendaria-project'
  version: 1
  source: string
  duration: number
  style: string
  language: string | null
  keep: Range[]
  cues: Cue[]
}

export type ModelOption = { name: string; size_mb?: number; notes?: string; installed: boolean }
export type Options = {
  models: ModelOption[]
  languages: { code: string; name: string }[]
  styles: string[]
  model: string
  language: string
  style: string
}

/** What the editor needs on load. `video` is null until a file is opened. */
export type State = Options & {
  video: string | null
  font: string // family name of the style's font, served by /api/font
  media: { width: number | null; height: number | null; fps: number | null; duration: number; has_audio: boolean }
  project: Project | null
}

export type Listing = {
  path: string
  parent: string | null
  home: string
  entries: { name: string; dir: boolean; size: number }[]
}

export type GlossaryState = { active: string; names: string[]; text: string }

export type JobEvent = { event: string; [key: string]: unknown }

async function request<T>(method: string, url: string, body?: unknown): Promise<T> {
  const response = await fetch(url, {
    method,
    headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = await response.json()
  if (!response.ok) throw new Error(data.error ?? response.statusText)
  return data as T
}

export const loadState = () => request<State>('GET', '/api/state')

export const browse = (path?: string) => request<Listing>('GET', `/api/browse${path ? `?path=${encodeURIComponent(path)}` : ''}`)

export const openVideo = (path: string) => request<State>('POST', '/api/open', { path })

/** Send a dropped file to the server (it cannot see the original path), with progress 0..1. */
export function uploadVideo(file: File, onProgress: (fraction: number) => void): Promise<State> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `/api/upload?name=${encodeURIComponent(file.name)}`)
    xhr.upload.onprogress = (e) => e.lengthComputable && onProgress(e.loaded / e.total)
    xhr.onload = () => {
      const data = JSON.parse(xhr.responseText)
      if (xhr.status >= 200 && xhr.status < 300) resolve(data as State)
      else reject(new Error(data.error ?? xhr.statusText))
    }
    xhr.onerror = () => reject(new Error('Upload failed.'))
    xhr.send(file)
  })
}

export const loadGlossary = () => request<GlossaryState>('GET', '/api/glossary')
export const addGlossaryEntry = (entry: string) => request<{ added: boolean }>('POST', '/api/glossary/add', { entry })
export const importGlossary = (name: string, text: string) => request<GlossaryState>('POST', '/api/glossary/import', { name, text })
export const useGlossary = (name: string) => request<GlossaryState>('POST', '/api/glossary/use', { name })

/** A glossary correction for the cue that contains `start` (source seconds). */
export type Suggestion = { id: number; cue: number; start: number; before: string; after: string; reason: string }

export type Peaks = { per_sec: number; duration: number; peaks: number[] }

export const loadPeaks = () => request<Peaks>('GET', '/api/peaks')

export const loadReview = () => request<{ suggestions: Suggestion[] }>('GET', '/api/review').then((r) => r.suggestions)

export const saveProject = (project: Project) => request<Project>('PUT', '/api/project', project)

export async function previewAss(): Promise<string> {
  const response = await fetch('/api/preview.ass')
  if (!response.ok) throw new Error(response.statusText)
  return response.text()
}

/** Start a job and call `onEvent` for each event until `done` or `error`. */
export async function runJob(url: string, options: unknown, onEvent: (e: JobEvent) => void): Promise<JobEvent> {
  const { job } = await request<{ job: string }>('POST', url, options)
  return new Promise((resolve) => {
    const source = new EventSource(`/api/jobs/${job}/events`)
    source.onmessage = (message) => {
      const event = JSON.parse(message.data) as JobEvent
      onEvent(event)
      if (event.event === 'done' || event.event === 'error') {
        source.close()
        resolve(event)
      }
    }
    source.onerror = () => {
      source.close()
      resolve({ event: 'error', message: 'Lost connection to the server.' })
    }
  })
}
