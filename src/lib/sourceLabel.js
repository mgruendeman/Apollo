export const SOURCE_PREFIX_RE = /^Apollo \d+ (Flight Journal|Lunar Surface Journal) — /

export function stripSourcePrefix(label) {
  return label.replace(SOURCE_PREFIX_RE, '')
}
