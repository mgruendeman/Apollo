// Audio clips are original NASA mission recordings (public domain), hosted by the
// Apollo Flight Journal / Apollo Lunar Surface Journal (apollojournals.org), a
// long-running volunteer archive edited by Eric M. Jones and W. David Woods.
// Each moment links back to its source page for the full transcript and credit.

export const missions = [
  {
    id: '08',
    number: 8,
    name: 'Apollo 8',
    dates: 'December 21–27, 1968',
    crew: ['Frank Borman', 'James Lovell', 'William Anders'],
    summary:
      'The first crewed spacecraft to leave low Earth orbit, reach the Moon, and orbit it — ten lunar orbits on Christmas Eve, capped by a live reading from Genesis and the Earthrise photograph.',
    status: 'coming-soon',
    moments: [],
  },
  {
    id: '09',
    number: 9,
    name: 'Apollo 9',
    dates: 'March 3–13, 1969',
    crew: ['James McDivitt', 'David Scott', 'Rusty Schweickart'],
    summary:
      'The first crewed flight of the full Apollo hardware stack, testing the Lunar Module — including docking, undocking, and a solo flight — in Earth orbit.',
    status: 'coming-soon',
    moments: [],
  },
  {
    id: '10',
    number: 10,
    name: 'Apollo 10',
    dates: 'May 18–26, 1969',
    crew: ['Thomas Stafford', 'John Young', 'Gene Cernan'],
    summary:
      'The "dress rehearsal" for the first landing: a full lunar-orbit run-through, with the Lunar Module descending to within 8.4 nautical miles of the surface.',
    status: 'coming-soon',
    moments: [],
  },
  {
    id: '12',
    number: 12,
    name: 'Apollo 12',
    dates: 'November 14–24, 1969',
    crew: ['Pete Conrad', 'Dick Gordon', 'Alan Bean'],
    summary:
      'Struck by lightning twice in its first minute of flight, Apollo 12 went on to land within walking distance of the Surveyor 3 probe for the second crewed Moon landing.',
    status: 'available',
    moments: [
      {
        id: 'sce-to-aux',
        get: '000:00:00',
        title: '"SCE to Aux" — Lightning Strike at Launch',
        description:
          'Thirty-six seconds after liftoff, Apollo 12 is struck by lightning; a second strike at 52 seconds knocks out telemetry and tumbles the guidance platform. EECOM John Aaron recognizes the garbled data pattern from a training run months earlier and calls for an obscure switch to be thrown: "Try SCE to auxiliary."',
        audioUrl:
          'https://apollojournals.org/afj/ap12fj/audio/a12a_000_00_00.mp3',
        sourceUrl: 'https://apollojournals.org/afj/ap12fj/01launch_to_earth_orbit.html',
        sourceLabel: 'Apollo 12 Flight Journal — Launch and Reaching Earth Orbit',
      },
      {
        id: 'whoopie',
        get: '115:15:26',
        title: 'First Steps & "Whoopie!"',
        description:
          'Pete Conrad becomes the third person to walk on the Moon. At 5-foot-6, the shortest of the Apollo commanders, he opens not with a rehearsed line but a grin and a "Whoopie!" — settling a bet with a reporter who\'d suggested NASA scripted Neil Armstrong\'s words.',
        audioUrl: 'https://apollojournals.org/alsj/a12/a12a.1151543.mp3',
        sourceUrl: 'https://apollojournals.org/alsj/a12/a12.eva1prelim.html',
        sourceLabel: 'Apollo 12 Lunar Surface Journal — First Steps',
      },
      {
        id: 'surveyor-inspect',
        get: '133:46:01',
        title: 'Inspecting Surveyor 3',
        description:
          'Conrad and Bean climb down into Surveyor Crater to reach Surveyor 3, an uncrewed probe that had been sitting exposed on the Moon since April 1967. They describe its sandblasted, discolored surface — a first look at how lunar dust and radiation weather hardware over years.',
        audioUrl: 'https://apollojournals.org/alsj/a12/a12a.1334601.mp3',
        sourceUrl: 'https://apollojournals.org/alsj/a12/a12.surveyor.html',
        sourceLabel: 'Apollo 12 Lunar Surface Journal — Surveyor Crater and Surveyor III',
      },
      {
        id: 'surveyor-cut',
        get: '134:28:58',
        title: 'Cutting Pieces off Surveyor 3',
        description:
          'The crew removes the TV camera and a sample tube from Surveyor 3 with cutting tools, bringing them home so engineers can study the effects of more than two and a half years of lunar surface exposure.',
        audioUrl: 'https://apollojournals.org/alsj/a12/a12a.1342858.mp3',
        sourceUrl: 'https://apollojournals.org/alsj/a12/a12.surveyor.html',
        sourceLabel: 'Apollo 12 Lunar Surface Journal — Surveyor Crater and Surveyor III',
      },
      {
        id: 'splashdown',
        get: '244:22:30',
        title: 'Splashdown',
        description:
          'Command Module Yankee Clipper comes through blackout and splashes down in the Pacific, closing out a ten-day mission that proved Apollo could land with precision at a chosen target.',
        audioUrl:
          'https://apollojournals.org/afj/ap12fj/audio/a12a_244_22_30_to_244_36_24.mp3',
        sourceUrl: 'https://apollojournals.org/afj/ap12fj/24day10_sf3th.html',
        sourceLabel: 'Apollo 12 Flight Journal — Day 10: Splashdown',
      },
    ],
  },
  {
    id: '14',
    number: 14,
    name: 'Apollo 14',
    dates: 'January 31 – February 9, 1971',
    crew: ['Alan Shepard', 'Stuart Roosa', 'Edgar Mitchell'],
    summary:
      'America\'s first astronaut in space returns to fly the third Moon landing, hauling a two-wheeled cart up Cone Crater and famously hitting two golf balls before leaving the surface.',
    status: 'coming-soon',
    moments: [],
  },
  {
    id: '15',
    number: 15,
    name: 'Apollo 15',
    dates: 'July 26 – August 7, 1971',
    crew: ['David Scott', 'Al Worden', 'James Irwin'],
    summary:
      'The first of the extended "J missions": a longer stay, a heavier scientific payload, and the first Lunar Roving Vehicle, which let the crew range miles from the lander to Hadley Rille.',
    status: 'available',
    moments: [
      {
        id: 'launch',
        get: '000:00:13',
        title: 'Launch — "Tower Clear"',
        description:
          'Apollo 15 clears the launch tower and control passes from the Cape to Mission Control in Houston, opening the first of the extended "J missions" with a longer stay and a car on the Moon.',
        audioUrl: 'https://apollojournals.org/afj/ap15fj/audio/a15_0000013.mp3',
        sourceUrl: 'https://apollojournals.org/afj/ap15fj/01launch_to_earth_orbit.html',
        sourceLabel: 'Apollo 15 Flight Journal — Launch and Reaching Earth Orbit',
      },
      {
        id: 'lrv-deploy',
        get: '119:52:55',
        title: 'Deploying the Lunar Roving Vehicle',
        description:
          'Scott and Irwin unfold and lower the first Lunar Roving Vehicle from its bay on the side of the Lunar Module — a fold-out electric car that will let them explore far beyond walking range.',
        audioUrl: 'https://apollojournals.org/alsj/a15/a15a1195255.mp3',
        sourceUrl: 'https://apollojournals.org/alsj/a15/a15.lrvdep.html',
        sourceLabel: 'Apollo 15 Lunar Surface Journal — Deploying the Lunar Roving Vehicle',
      },
      {
        id: 'lrv-checkout',
        get: '120:13:34',
        title: 'Loading and Checking Out the Rover',
        description:
          'With the Rover unfolded, the crew finishes rigging its tools, seats, and fenders and runs a steering and drive checkout before taking it out for its first ride across the Moon.',
        audioUrl: 'https://apollojournals.org/alsj/a15/a15a1201334.mp3',
        sourceUrl: 'https://apollojournals.org/alsj/a15/a15.lrvdep.html',
        sourceLabel: 'Apollo 15 Lunar Surface Journal — Deploying the Lunar Roving Vehicle',
      },
      {
        id: 'genesis-rock',
        get: '145:47:47',
        title: 'The Genesis Rock',
        description:
          'Near the rim of Spur Crater, Scott spots a whitish, crystalline rock unlike anything sampled so far. Later nicknamed the "Genesis Rock," it turns out to be a roughly 4.1-billion-year-old piece of the Moon\'s original crust — one of the oldest samples ever brought back.',
        audioUrl: 'https://apollojournals.org/alsj/a15/a15a1454747.mp3',
        sourceUrl: 'https://apollojournals.org/alsj/a15/a15.spur.html',
        sourceLabel: 'Apollo 15 Lunar Surface Journal — Spur Crater',
      },
      {
        id: 'hadley-rille-1',
        get: '165:17:03',
        title: 'At the Edge of Hadley Rille',
        description:
          'On the third EVA, Scott and Irwin drive the Rover to the lip of Hadley Rille, a mile-wide, 1,200-foot-deep sinuous canyon, and describe its terraced, layered walls to geologists back in Houston.',
        audioUrl: 'https://apollojournals.org/alsj/a15/a15a1651703.mp3',
        sourceUrl: 'https://apollojournals.org/alsj/a15/a15.rille.html',
        sourceLabel: 'Apollo 15 Lunar Surface Journal — Hadley Rille',
      },
      {
        id: 'hadley-rille-2',
        get: '165:29:51',
        title: 'Hadley Rille, Continued',
        description:
          'The crew continues describing and photographing the rille\'s exposed rock layers, evidence used for decades afterward to help settle how these giant lunar channels formed.',
        audioUrl: 'https://apollojournals.org/alsj/a15/a15a1652951.mp3',
        sourceUrl: 'https://apollojournals.org/alsj/a15/a15.rille.html',
        sourceLabel: 'Apollo 15 Lunar Surface Journal — Hadley Rille',
      },
    ],
  },
  {
    id: '16',
    number: 16,
    name: 'Apollo 16',
    dates: 'April 16–27, 1972',
    crew: ['John Young', 'Ken Mattingly', 'Charlie Duke'],
    summary:
      'The first landing in the lunar highlands, at the Descartes region, returning the largest single rock collected during the program — the 11.7 kg "Big Muley."',
    status: 'coming-soon',
    moments: [],
  },
]

export const alreadyCovered = {
  label: 'Apollo 11, 13 & 17',
  note: 'Already covered in full, second-by-second, by Apollo in Real Time.',
  url: 'https://apolloinrealtime.org/',
}

export function findMission(id) {
  return missions.find((m) => m.id === id)
}
