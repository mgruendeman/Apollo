// How long a line takes to say, roughly: about 11 letters a second (the
// pace of the long lines on the tapes), and figures read out a digit at a
// time (NASA's PADs and readbacks).
export function sayingSeconds(text) {
  const digits = (text.match(/\d/g) || []).length
  const letters = (text.match(/[A-Za-z]/g) || []).length
  return 2 + letters * 0.09 + digits * 0.4
}

// Title and details for a report about one transcript line, so the report
// says exactly which line and where in which recording. `nextOffset` is
// where the next line starts, so replaying the line can run to it.
export function lineReport({ missionName, clipId, audioUrl, sourceUrl, audioAt }, line, offsetSeconds, nextOffset) {
  const at = Math.max(0, Math.round(offsetSeconds || 0))
  const clock = `${Math.floor(at / 60)}:${String(at % 60).padStart(2, '0')}`
  // the second in the audio file where the line plays: a clip's offset, or the tape's
  const playAt = audioAt ? audioAt(offsetSeconds) : at
  // play the whole line: its likely length, or on to the next line if that
  // starts within about twice that; at least 10 s, at most 3 minutes
  let length = sayingSeconds(line.text)
  if (nextOffset != null && nextOffset > offsetSeconds + length && nextOffset < offsetSeconds + 2 * length + 10)
    length = nextOffset - offsetSeconds
  length = Math.min(180, Math.max(10, length + 1.5))
  return {
    title: `${missionName} GET ${line.get}: transcript line`,
    audio: audioUrl && playAt != null ? { url: audioUrl, at: playAt, until: playAt + length } : null,
    context: [
      `${line.speaker}: "${line.text}"`,
      line.clip ? `GET ${line.get}, in ${clipId}` : `GET ${line.get}, ${clock} into clip ${clipId}`,
      audioUrl && `Audio: ${audioUrl}`,
      sourceUrl && `Source: ${sourceUrl}`,
    ]
      .filter(Boolean)
      .join('\n'),
  }
}
