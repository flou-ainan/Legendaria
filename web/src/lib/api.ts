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

export type State = {
  video: string
  font: string // family name of the style's font, served by /api/font
  media: { width: number | null; height: number | null; fps: number | null; duration: number; has_audio: boolean }
  project: Project | null
  styles: string[]
  style: string
  model: string
  language: string
}

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
