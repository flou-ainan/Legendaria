// The video picked on this device is played from the device itself (plan 11, A): the upload exists for the
// server's jobs (transcription, export), so the same bytes do not travel back to be played.

/** `url` is an object URL of the picked file, or null to stream from the server (`/api/media`). */
export const localMedia = $state<{ url: string | null }>({ url: null })

/** Play this file from memory (null: go back to the server's copy). Not kept across a reload: the server's copy takes over. */
export function useLocalFile(file: File | null) {
  if (localMedia.url) URL.revokeObjectURL(localMedia.url)
  localMedia.url = file ? URL.createObjectURL(file) : null
}
