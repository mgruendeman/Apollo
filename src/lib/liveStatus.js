// "This many years ago today" — checks whether the current moment falls
// within [this year's anniversary of launch, anniversary + mission
// duration]. None of these six missions' real flights crossed a calendar
// year boundary, so only the current year's anniversary needs checking.

export function getLiveStatus(mission, now = new Date()) {
  if (!mission.launchUtc || !mission.durationSeconds) return null
  const launch = new Date(mission.launchUtc)
  const year = now.getUTCFullYear()
  const anniversary = new Date(
    Date.UTC(
      year,
      launch.getUTCMonth(),
      launch.getUTCDate(),
      launch.getUTCHours(),
      launch.getUTCMinutes(),
      launch.getUTCSeconds(),
    ),
  )
  const elapsedSeconds = Math.floor((now - anniversary) / 1000)
  if (elapsedSeconds < 0 || elapsedSeconds > mission.durationSeconds) return null
  return {
    getSeconds: elapsedSeconds,
    yearsAgo: year - launch.getUTCFullYear(),
  }
}

export function getAllLiveMissions(missions, now = new Date()) {
  return missions
    .map((mission) => {
      const status = getLiveStatus(mission, now)
      return status ? { mission, ...status } : null
    })
    .filter(Boolean)
}

export function formatGet(totalSeconds) {
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  const s = Math.floor(totalSeconds % 60)
  return `${String(h).padStart(3, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
