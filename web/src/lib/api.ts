// Talks to `flosub serve` (engine/legendaria_engine/server.py).
import type { Range } from './timeline'
import { useLocalFile } from './localmedia.svelte'

export type Word = { start: number; end: number; word: string; probability?: number }
export type Cue = { start: number; end: number; text: string; words?: Word[]; look?: Look } // `look`: this cue's own overrides (ADR-022)

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
  look?: Look // optional overrides of the style (ADR-019)
}

/** `size` multiplies the style's font size; `y` is the text centre's height above the bottom (0 to 1). */
export type Look = {
  font?: string; size?: number; y?: number; color?: string; outline_color?: string; outline?: number; uppercase?: boolean
  shadow?: number; shadow_on?: boolean; shadow_color?: string; shadow_opacity?: number
  box?: boolean; box_color?: string; box_opacity?: number; box_padding_x?: number; box_padding_y?: number; box_radius?: number
}
/** What the style itself sets, for the Look menu (every override has a value here). */
export type BaseLook = Required<Omit<Look, 'size'>>

export type FontEntry = { family: string; file: string; bold: boolean; category: string }

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
  api?: number
  video: string | null
  path?: string // full path of the open video (to reopen it after a restart)
  font: string // family name of the font in use, served by /api/font
  fonts: FontEntry[] // the bundled families, served by /api/fonts/<file>
  base: BaseLook // what the style itself sets, for the Look menu
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

/** A failed request: `code` is a stable key from the server (`sign_in`, `wrong_password`...), `retryAfter` is in seconds. */
export class ApiError extends Error {
  constructor(message: string, readonly status: number, readonly code?: string, readonly retryAfter?: number) {
    super(message)
  }
}

/** Fired when the server says the session is gone (the password changed, or it expired): the page shows the sign-in. */
export const SIGN_IN_EVENT = 'legendaria:sign-in'

async function request<T>(method: string, url: string, body?: unknown): Promise<T> {
  const response = await fetch(url, {
    method,
    headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    if (data.code === 'sign_in') window.dispatchEvent(new Event(SIGN_IN_EVENT))
    throw new ApiError(data.error ?? response.statusText, response.status, data.code, Number(response.headers.get('Retry-After')) || undefined)
  }
  return data as T
}

/** The server API this page was built for (server.py API_VERSION); a different one means `flosub serve` is older. */
export const API_VERSION = 6

/** Who is asking and where else the editor can be opened (`/api/access`, open to anyone who reached the server). */
export type AccessState = { password_set: boolean; signed_in: boolean; remote: boolean; can_browse: boolean; addresses: string[] }

export const loadAccess = () => request<AccessState>('GET', '/api/access')
export const signIn = (password: string) => request<{ ok: true }>('POST', '/api/login', { password })
export const signOut = () => request<{ ok: true }>('POST', '/api/logout')
export const changePassword = (current: string, next: string) => request<{ ok: true }>('POST', '/api/access/password', { current, new: next })

export const loadState = () => request<State>('GET', '/api/state')

export const browse = (path?: string) => request<Listing>('GET', `/api/browse${path ? `?path=${encodeURIComponent(path)}` : ''}`)

export const openVideo = async (path: string) => {
  const state = await request<State>('POST', '/api/open', { path })
  useLocalFile(null) // a file on the computer is streamed by the server
  return state
}

/** Send a dropped file to the server (it cannot see the original path), with progress 0..1. */
export function uploadVideo(file: File, onProgress: (fraction: number) => void): Promise<State> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `/api/upload?name=${encodeURIComponent(file.name)}`)
    xhr.upload.onprogress = (e) => e.lengthComputable && onProgress(e.loaded / e.total)
    xhr.onload = () => {
      const data = JSON.parse(xhr.responseText)
      if (xhr.status >= 200 && xhr.status < 300) {
        useLocalFile(file) // play the picked file here; the upload is only for the server's jobs
        resolve(data as State)
      }
      else {
        if (data.code === 'sign_in') window.dispatchEvent(new Event(SIGN_IN_EVENT))
        reject(new ApiError(data.error ?? xhr.statusText, xhr.status, data.code))
      }
    }
    xhr.onerror = () => reject(new Error('Upload failed.'))
    xhr.send(file)
  })
}

/** Open the browser's own file picker (the client's files, not the server's); null if cancelled. */
export function pickFile(accept = 'video/*,audio/*'): Promise<File | null> {
  return new Promise((resolve) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = accept
    input.onchange = () => resolve(input.files?.[0] ?? null)
    input.oncancel = () => resolve(null)
    input.click()
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
