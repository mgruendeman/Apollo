// Full-length NASA recordings from the Johnson Space Center Audio Control
// Room's uploads to the Internet Archive (public domain). Unlike the
// journal clips these aren't cut or timed to GET, so they're offered as
// whole recordings rather than on the synced timeline.

export const archiveRecordings = {
  '09': {
    collection: 'https://archive.org/details/Apollo9',
    hoursInCollection: 50,
    recordings: [
      {
        id: 'AS-9_DSEA',
        title: 'Lunar Module Spider onboard tape (DSEA)',
        description:
          'The recorder aboard Spider, capturing the crew inside the Lunar Module. NASA reconstructed it by hand from the original tape, provided by the Smithsonian National Air and Space Museum.',
        url: 'https://archive.org/download/Apollo9/AS-9_DSEA.mp3',
        durationSeconds: 19264,
      },
      {
        id: 'Apollo9Post-missionPressConference',
        title: 'Post-mission press conference',
        description: 'McDivitt, Scott and Schweickart talk through the flight with the press after their return.',
        url: 'https://archive.org/download/Apollo9/Apollo9Post-missionPressConference.mp3',
        durationSeconds: 6046,
      },
    ],
  },
  '11': {
    collection: 'https://archive.org/details/Apollo11Audio',
    hoursInCollection: 174,
    recordings: [],
  },
  '13': {
    collection: 'https://archive.org/details/Apollo13Audio',
    hoursInCollection: 1094,
    recordings: [
      {
        id: 'Apollo-13-Problem',
        title: '"Houston, we\'ve had a problem"',
        description: 'NASA\'s own 98-minute recording spanning the oxygen tank explosion and the hour and a half that followed.',
        url: 'https://archive.org/download/Apollo13Audio/Apollo-13-Problem.mp3',
        durationSeconds: 5894,
      },
      {
        id: 'EECOM-Loop-During-Accident',
        title: 'The EECOM loop during the accident',
        description:
          'The Mission Control console loop of EECOM Sy Liebergot and his back room as the oxygen tank readings went wrong: the controllers working the problem, not the crew.',
        url: 'https://archive.org/download/Apollo13Audio/EECOM-Loop-During-Accident.mp3',
        durationSeconds: 1426,
      },
    ],
  },
}
