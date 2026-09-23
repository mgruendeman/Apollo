// Title and details for a report about one transcript line, so the report
// says exactly which line and where in which recording.
export function lineReport({ missionName, clipId, audioUrl, sourceUrl }, line, offsetSeconds) {
  const at = Math.max(0, Math.round(offsetSeconds || 0))
  const clock = `${Math.floor(at / 60)}:${String(at % 60).padStart(2, '0')}`
  return {
    title: `${missionName} GET ${line.get}: transcript line`,
    context: [
      `${line.speaker}: "${line.text}"`,
      `GET ${line.get}, ${clock} into clip ${clipId}`,
      audioUrl && `Audio: ${audioUrl}`,
      sourceUrl && `Source: ${sourceUrl}`,
    ]
      .filter(Boolean)
      .join('\n'),
  }
}
