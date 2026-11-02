// Same alphabet as the engine's `access.generate_password`: no l, o, 0 or 1, 32 symbols so a byte maps evenly.
const ALPHABET = 'abcdefghijkmnpqrstuvwxyz23456789'

/** A random `xxxx-xxxx-xxxx` password (60 bits), easy to read out and to type on a phone. */
export function generatePassword(random: (n: number) => Uint8Array = (n) => crypto.getRandomValues(new Uint8Array(n))): string {
  const symbols = Array.from(random(12), (byte) => ALPHABET[byte & 31])
  return [0, 4, 8].map((i) => symbols.slice(i, i + 4).join('')).join('-')
}
