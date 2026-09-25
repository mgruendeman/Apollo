// Title and details for a report about one transcript line, so the report
// says exactly which line and where in which recording.
export function lineReport({ missionName, clipId, audioUrl, sourceUrl, audioAt }, line, offsetSeconds) {
  const at = Math.max(0, Math.round(offsetSeconds || 0))
  const clock = `${Math.floor(at / 60)}:${String(at % 60).padStart(2, '0')}`
  // the second in the audio file where the line plays: a clip's offset, or the tape's
  const playAt = audioAt ? audioAt(offsetSeconds) : at
  return {
    title: `${missionName} GET ${line.get}: transcript line`,
    audio: audioUrl && playAt != null ? { url: audioUrl, at: playAt } : null,
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
