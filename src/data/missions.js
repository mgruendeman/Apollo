// Mission metadata. Missions with a `timeline` play NASA's own tapes end
// to end, with NASA's transcript timed to them (public/timeline/<id>.json,
// built by pipeline/align_tapes.py). The rest, until their tapes are done,
// play clips from the Apollo Flight Journal and Apollo Lunar Surface
// Journal (apollojournals.org): src/data/clips/<id>.json (clip index) and
// public/transcripts/<id>.json (per-clip transcript lines), from
// scripts/scrape.py.
//
// A tape mission's `events` are the mission times (GET) that divide its
// flight phases, from NASA's "Apollo by the Numbers" (SP-2000-4029, the
// mission timelines): translunar injection, lunar orbit insertion ignition,
// lunar liftoff ignition, LM ascent stage jettison, transearth injection
// ignition and CM/SM separation. Its highlights are moments on the tapes.

// Landing coordinates are the LM positions from NASA NSSDCA's Apollo
// landing site table (LRO-derived, Wagner et al. 2017).
export const missions = [
  {
    id: '08',
    number: 8,
    name: 'Apollo 8',
    dates: 'December 21–27, 1968',
    crew: ['Frank Borman', 'James Lovell', 'William Anders'],
    summary:
      'The first crewed spacecraft to leave low Earth orbit, reach the Moon, and orbit it — ten lunar orbits on Christmas Eve, capped by a live reading from Genesis and the Earthrise photograph.',
    status: 'available',
    timeline: 'apollo08', // whole-mission tapes: public/timeline/apollo08.json
    launchUtc: '1968-12-21T12:51:00Z',
    durationSeconds: 529242, // 147:00:42
    // (archive.org's Apollo 8 tapes are 000-AAA to 049-AAA and 056-AAA; 013, 037 and 045 are held backward there and are turned on disk)
    tapesNote: "NASA's typed transcript of this flight survives only as a rough scan, so more of its lines are flagged for a listen than on the later missions.",
    events: { tli: '002:56:06', loi: '069:08:20', tei: '089:19:17', cmSep: '146:28:48' },
    csmName: null,
    lmName: null,
    spacecraftNote: 'The Command Module had no name (it flew as "Apollo 8"), and there was no Lunar Module; a dummy test article rode in its place.',
    objective: 'Fly the first crew to the Moon: ten orbits to prove the spacecraft, navigation and communications for a landing, and to photograph candidate landing sites.',
    highlights: [
      { id: 'a08-launch', at: '-000:00:30', title: 'Launch: the first crew on a Saturn V' },
      { id: 'a08-tli', at: '002:27:00', title: '"You are GO for TLI": leaving Earth' },
      { id: 'a08-earthrise', at: '075:49:20', title: 'Earthrise' },
      { id: 'a08-genesis', at: '086:06:40', title: 'Christmas Eve: the Genesis reading' },
      { id: 'a08-santa', at: '089:34:10', title: '"Please be informed there is a Santa Claus"' },
      { id: 'a08-splashdown', at: '146:58:30', title: 'Splashdown' },
    ],
  },
  {
    id: '09',
    number: 9,
    name: 'Apollo 9',
    dates: 'March 3–13, 1969',
    crew: ['James McDivitt', 'David Scott', 'Rusty Schweickart'],
    summary:
      'The first crewed flight of the full Apollo hardware stack, testing the Lunar Module — including docking, undocking, and a solo flight — in Earth orbit.',
    status: 'available',
    timeline: 'apollo09', // whole-mission tapes: public/timeline/apollo09.json
    launchUtc: '1969-03-03T16:00:00Z',
    durationSeconds: 867654, // 241:00:54
    // (archive.org's Apollo 9 tapes are 065-AAA to 085-AAA, without 068, 069 and 078; 079 is a stub; they end at 189 hours)
    tapesNote: "Apollo 9 never left Earth orbit, so its tapes run out of contact for most of each 90-minute orbit, between the tracking stations. NASA's tapes of this flight stop at 189 hours, two days before splashdown.",
    // Earth-orbit flight: no translunar injection; the Lunar Module's docking, the spacewalk and the solo flight instead
    events: {
      docking: '003:01:59', evaStart: '072:59:02', evaEnd: '073:49:56', undocking: '092:39:36', redocking: '099:02:26',
      lmJettison: '101:22:45', cmSep: '240:36:04',
    },
    csmName: 'Gumdrop',
    lmName: 'Spider',
    objective: 'Fly the complete Apollo spacecraft for the first time, in Earth orbit: dock with the Lunar Module, test the lunar spacesuit and backpack outside the spacecraft, and fly Spider on its own and rendezvous back with Gumdrop, as a lunar landing crew would.',
    landingNote: 'None: Apollo 9 stayed in Earth orbit, testing the Lunar Module.',
    highlights: [
      { id: 'a09-launch', at: '-000:00:30', title: 'Launch' },
      { id: 'a09-docking', at: '003:01:40', title: 'Docking with Spider' },
      { id: 'a09-eva', at: '073:02:00', title: 'Schweickart on the porch: the spacesuit\'s first flight' },
      { id: 'a09-undocking', at: '092:38:00', title: 'Spider flies alone' },
      { id: 'a09-rendezvous', at: '099:00:00', title: 'Spider and Gumdrop dock again' },
      { id: 'a09-last-burn', at: '101:52:30', title: "Spider's last burn, fired until the tank ran dry" },
    ],
  },
  {
    id: '10',
    number: 10,
    name: 'Apollo 10',
    dates: 'May 18–26, 1969',
    crew: ['Thomas Stafford', 'John Young', 'Gene Cernan'],
    summary:
      'The "dress rehearsal" for the first landing: a full lunar-orbit run-through, with the Lunar Module descending to within 8.4 nautical miles of the surface.',
    status: 'available',
    clipsFile: 'apollo10',
    clipCount: 184,
    launchUtc: '1969-05-18T16:49:00Z',
    durationSeconds: 691403, // 192:03:23
    csmName: 'Charlie Brown',
    lmName: 'Snoopy',
    objective: 'Rehearse every step of a landing except the touchdown itself, with Snoopy swooping low over the planned Apollo 11 landing area before rejoining Charlie Brown.',
    highlights: [
      { id: 'a10-0000254', title: 'Launch' },
      { id: 'a10-s-ivb-sep-0035600', title: '"Snoopy\'s coming out of the doghouse"' },
    ],
  },
  {
    id: '11',
    number: 11,
    name: 'Apollo 11',
    dates: 'July 16–24, 1969',
    crew: ['Neil Armstrong', 'Michael Collins', 'Buzz Aldrin'],
    summary:
      'The first crewed Moon landing. Armstrong and Aldrin spend two and a quarter hours on the surface at Tranquility Base while Collins orbits alone above them.',
    status: 'available',
    timeline: 'apollo11', // whole-mission tapes: public/timeline/apollo11.json
    launchUtc: '1969-07-16T13:32:00Z',
    durationSeconds: 703115, // 195:18:35
    landingSeconds: 369940, // touchdown at GET 102:45:40
    events: { tli: '002:50:13', loi: '075:49:50', liftoff: '124:22:01', lmJettison: '130:09:31', tei: '135:23:42', cmSep: '194:49:13' },
    csmName: 'Columbia',
    lmName: 'Eagle',
    objective: 'Land two astronauts on the Moon and return them safely to Earth, the goal President Kennedy set in 1961.',
    landingSite: { name: 'Tranquility Base, Sea of Tranquility (Mare Tranquillitatis)', lat: 0.67416, lon: 23.47314 },
    highlights: [
      { id: 'a11-launch', at: '-000:00:30', title: 'Launch' },
      { id: 'a11-landing', at: '102:45:40', title: '"The Eagle has landed"' },
      { id: 'a11-first-step', at: '109:24:13', title: '"One small step..."' },
    ],
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
    timeline: 'apollo12', // whole-mission tapes: public/timeline/apollo12.json
    launchUtc: '1969-11-14T16:22:00Z',
    durationSeconds: 880584, // 244:36:24
    landingSeconds: 397956, // touchdown at GET 110:32:36
    events: { tli: '002:53:14', loi: '083:25:23', liftoff: '142:03:48', lmJettison: '147:59:32', tei: '172:27:17', cmSep: '244:07:20' },
    csmName: 'Yankee Clipper',
    lmName: 'Intrepid',
    objective: 'Prove a pinpoint landing by setting down next to the robotic Surveyor 3 lander, and set up the first full ALSEP science station.',
    landingSite: { name: 'Ocean of Storms (Oceanus Procellarum), beside the Surveyor 3 probe', lat: -3.0128, lon: -23.4219 },
    highlights: [
      { id: 'a12-lightning', at: '000:00:25', title: '"SCE to Aux" — lightning strike at launch' },
      { id: 'a12-first-steps', at: '115:22:00', title: 'First steps & "Whoopie!"' },
      { id: 'a12-surveyor', at: '133:55:30', title: 'Inspecting Surveyor 3' },
      { id: 'a12-splashdown', at: '244:30:40', title: 'Splashdown' },
    ],
  },
  {
    id: '13',
    number: 13,
    name: 'Apollo 13',
    dates: 'April 11–17, 1970',
    crew: ['Jim Lovell', 'Jack Swigert', 'Fred Haise'],
    summary:
      'An oxygen tank explosion two days out crippled the Service Module and scrapped the Moon landing — the crew looped around the Moon and used the Lunar Module as a lifeboat to get home.',
    status: 'available',
    clipsFile: 'apollo13',
    clipCount: 237,
    launchUtc: '1970-04-11T19:13:00Z',
    durationSeconds: 514481, // 142:54:41
    csmName: 'Odyssey',
    lmName: 'Aquarius',
    objective: 'Planned as the third landing, at the Fra Mauro highlands. After the oxygen tank explosion two days out, the objective became getting the crew home alive.',
    plannedSite: { name: 'Fra Mauro highlands (planned; Apollo 14 later landed there)', lat: -3.64589, lon: -17.47194 },
    highlights: [
      { id: 'a13_0000002ag', title: 'Launch' },
      { id: 'a13_0555519', title: '"Houston, we\'ve had a problem"' },
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
    status: 'available',
    timeline: 'apollo14', // whole-mission tapes: public/timeline/apollo14.json
    launchUtc: '1971-01-31T21:03:02Z',
    durationSeconds: 777718, // 216:01:58
    landingSeconds: 389709, // touchdown at GET 108:15:09
    tapesNote: "Times here run from liftoff; from 55 hours on, the announcer's times are 40 minutes ahead, because Mission Control set its clock forward to make up for the launch's weather hold.",
    events: { tli: '002:34:33', loi: '081:56:41', liftoff: '141:45:40', lmJettison: '145:44:58', tei: '148:36:02', cmSep: '215:32:42' },
    csmName: 'Kitty Hawk',
    lmName: 'Antares',
    objective: 'Sample the Fra Mauro formation, thought to be debris thrown out by the impact that formed Mare Imbrium, including the rim of Cone Crater.',
    landingSite: { name: 'Fra Mauro highlands', lat: -3.64589, lon: -17.47194 },
    highlights: [
      { id: 'a14-launch', at: '-000:00:30', title: 'Launch' },
      { id: 'a14-golf', at: '135:08:00', title: 'Shepard hits golf balls on the Moon' },
    ],
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
    timeline: 'apollo15', // whole-mission tapes: public/timeline/apollo15.json
    launchUtc: '1971-07-26T13:34:00Z',
    durationSeconds: 1062713, // 295:11:53
    landingSeconds: 376949, // touchdown at GET 104:42:29
    // (archive.org's Apollo 15 tapes are 540-AAA to 583-AAA)
    tapesNote: "NASA's tapes on archive.org stop at 199 hours, in lunar orbit: the trip home has no recording here.",
    events: { tli: '002:56:03', loi: '078:31:47', liftoff: '171:37:23', lmJettison: '179:30:01', tei: '223:48:46', cmSep: '294:43:55' },
    csmName: 'Endeavour',
    lmName: 'Falcon',
    objective: 'Fly the first extended "J" mission: three days on the surface, the first Lunar Roving Vehicle, and geology at Hadley Rille and the Apennine front.',
    landingSite: { name: 'Hadley–Apennine, between Hadley Rille and the Apennine Mountains', lat: 26.13239, lon: 3.6333 },
    highlights: [
      { id: 'a15-launch', at: '-000:00:30', title: 'Launch' },
      { id: 'a15-rover', at: '119:52:55', title: 'Deploying the Lunar Roving Vehicle' },
      { id: 'a15-genesis', at: '145:47:47', title: 'The Genesis Rock' },
      { id: 'a15-rille', at: '165:17:03', title: 'At the edge of Hadley Rille' },
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
    status: 'available',
    timeline: 'apollo16', // whole-mission tapes: public/timeline/apollo16.json
    launchUtc: '1972-04-16T17:54:00Z',
    durationSeconds: 957065, // 265:51:05
    landingSeconds: 376175, // touchdown at GET 104:29:35
    // (archive.org's Apollo 16 tapes are 657-AAA to 710-AAA, without 684 and 685)
    tapesNote: "Two of NASA's tapes are missing from archive.org: from 122:14 to 125:23, the end of the first moonwalk, there's no recording here. Times here run from liftoff; the announcer's times are 12 minutes ahead from 118 hours on and 24 hours 46 minutes ahead from 202 hours on, because Mission Control twice set its clock forward to match the flight plan.",
    events: { tli: '002:39:28', loi: '074:28:28', liftoff: '175:31:48', lmJettison: '195:00:12', tei: '200:21:33', cmSep: '265:22:23' },
    csmName: 'Casper',
    lmName: 'Orion',
    objective: 'Make the first landing in the lunar highlands, to sample rock that geologists expected to be volcanic (it turned out to be impact breccia).',
    landingSite: { name: 'Descartes Highlands', lat: -8.9734, lon: 15.5011 },
    highlights: [
      { id: 'a16-launch', at: '-000:00:30', title: 'Launch' },
      { id: 'a16-landing', at: '104:26:50', title: 'Landing at Descartes' },
      { id: 'a16-salute', at: '120:25:10', title: "John Young's jump salute" },
      { id: 'a16-liftoff', at: '175:31:20', title: 'Liftoff from the Moon' },
      { id: 'a16-ken-eva', at: '218:56:30', title: "Ken Mattingly's spacewalk" },
    ],
  },
  {
    id: '17',
    number: 17,
    name: 'Apollo 17',
    dates: 'December 7–19, 1972',
    crew: ['Gene Cernan', 'Ronald Evans', 'Harrison Schmitt'],
    summary:
      'The last Apollo Moon mission and the only night launch, carrying the program\'s first scientist-astronaut for the longest stay, longest EVAs, and most samples of any landing.',
    status: 'available',
    timeline: 'apollo17', // whole-mission tapes: public/timeline/apollo17.json
    launchUtc: '1972-12-07T05:33:00Z',
    durationSeconds: 1086719, // 301:51:59
    // Times are from liftoff, as NASA's transcript keeps them. Mission Control
    // set its own clock ahead 2:40:00 at 65 hours (the launch was that late),
    // so the announcer's times from then on run 2:40 ahead of these.
    landingSeconds: 397318, // touchdown at GET 110:21:58
    // (archive.org's Apollo 17 tapes are 765-AAA to 830-AAA, without 793; 828 is a 7-second stub)
    tapesNote: "Two of NASA's tapes are missing from archive.org: there's no recording from 126:16 to 133:46, the first night on the Moon, or from 286:57 to 296:47, the last night before splashdown. Times here run from liftoff; from 65 hours on, the announcer's times are 2 hours 40 minutes ahead, because Mission Control set its clock forward to match the flight plan after the late launch.",
    events: { tli: '003:18:38', loi: '086:14:23', liftoff: '185:21:37', lmJettison: '191:18:31', tei: '234:02:09', cmSep: '301:23:49' },
    csmName: 'America',
    lmName: 'Challenger',
    objective: 'Close out Apollo with the longest landing: sample ancient highland rock from the valley walls and look for young volcanic material, with the first geologist on the Moon.',
    landingSite: { name: 'Taurus–Littrow valley, on the edge of the Sea of Serenity', lat: 20.1911, lon: 30.7723 },
    highlights: [
      { id: 'a17-launch', at: '-000:00:30', title: 'Launch — the only night launch' },
      { id: 'a17-landing', at: '110:19:30', title: '"The Challenger has landed"' },
      { id: 'a17-orange-soil', at: '142:46:10', title: 'Orange soil at Shorty crater' },
      { id: 'a17-farewell', at: '168:01:20', title: "Cernan's farewell to the Moon" },
      { id: 'a17-liftoff', at: '185:21:10', title: 'Liftoff from the Moon' },
      { id: 'a17-evans-eva', at: '254:59:40', title: "Ron Evans's spacewalk" },
    ],
  },
]

export function findMission(id) {
  return missions.find((m) => m.id === id)
}
