// A glossary of the jargon, hardware, and roles that come up constantly in
// the transcripts. Definitions are written from general historical/technical
// knowledge of the Apollo program; quotes are only included where they're a
// real, specific quote (not paraphrased or invented), and external links
// only where the target was verified to exist.
//
// `terms` is the list to match against transcript text: the first one wins
// on overlapping matches, so multi-word phrases are listed before the
// single words they contain.

export const glossary = [
  {
    id: 'get',
    terms: ['Ground Elapsed Time', 'GET'],
    short: 'Mission clock, counted from the moment of liftoff.',
    long: 'Ground Elapsed Time is the master clock for the whole mission: it starts at 000:00:00 at the instant of liftoff and counts up in hours, minutes and seconds from there — never resetting, even past 24 hours (a splashdown at GET 244:36:24 means 244 hours after launch, about 10 days in). Every timestamp in this archive is GET, not clock time. NASA later renamed the concept "Mission Elapsed Time" for the Space Shuttle.',
    links: [{ label: 'Wikipedia: Mission Elapsed Time', url: 'https://en.wikipedia.org/wiki/Mission_Elapsed_Time' }],
  },
  {
    id: 'csm',
    terms: ['Command and Service Module', 'Command Module', 'Service Module', 'CSM'],
    short: 'The mothership: crew cabin plus the engine/power/supplies module behind it.',
    long: 'The CSM was the part of the stack that flew all the way to the Moon and back to Earth. It had two pieces bolted together: the cone-shaped Command Module (CM), where the three-person crew lived, flew, and rode through reentry; and the cylindrical Service Module (SM), an unpressurized bay behind it carrying the main engine (the SPS), fuel cells, oxygen and hydrogen tanks, and other consumables. The SM was jettisoned and burned up in the atmosphere just before reentry — only the Command Module came home.',
    links: [{ label: 'Wikipedia: Apollo command and service module', url: 'https://en.wikipedia.org/wiki/Apollo_command_and_service_module' }],
  },
  {
    id: 'lm',
    terms: ['Lunar Module', 'LM', 'LEM'],
    short: 'The two-person lander that actually touched down on the Moon.',
    long: 'The Lunar Module was a dedicated, ungainly-looking spacecraft built only to fly from lunar orbit to the surface and back — it never touched Earth and was never designed to fly through an atmosphere. It had two stages: a descent stage with landing legs and the main landing engine, left behind on the Moon as a launch platform, and an ascent stage carrying the crew cabin, which lifted the two moonwalkers back into lunar orbit to redock with the CSM. Early in the program it was called the Lunar Excursion Module (LEM); NASA dropped "Excursion" from the official name but the old acronym stuck around in speech.',
    links: [{ label: 'Wikipedia: Lunar module', url: 'https://en.wikipedia.org/wiki/Lunar_module' }],
  },
  {
    id: 'eva',
    terms: ['Extravehicular Activity', 'EVA'],
    short: 'Any time an astronaut leaves the pressurized cabin — a moonwalk, most often.',
    long: 'EVA is NASA-speak for any activity outside a pressurized spacecraft. On landing missions it almost always means a moonwalk: astronauts in pressure suits, breathing from a backpack, working on the surface for several hours at a stretch. Missions with no landing (like Apollo 9 and 10) still had EVAs — spacewalks in Earth or lunar orbit to test the suit and hardware.',
  },
  {
    id: 'alsep',
    terms: ['ALSEP'],
    short: 'A set of science instruments the crew set up and left running on the Moon.',
    long: 'The Apollo Lunar Surface Experiments Package was a kit of instruments — typically a seismometer, a magnetometer, a solar wind detector, and others depending on the mission — that the crew unpacked and deployed a short walk from the lander. Powered by a small plutonium generator (so it kept working long after the crew left), each ALSEP radioed data back to Earth for years afterward.',
  },
  {
    id: 'sps',
    terms: ['Service Propulsion System', 'SPS'],
    short: 'The CSM\'s main rocket engine, used for every major course-changing burn.',
    long: 'A single restartable engine in the Service Module, the SPS did the heavy lifting for the CSM: lunar orbit insertion, the burn back out of lunar orbit (TEI), and any mid-course corrections along the way. It had no backup — a failed SPS burn to leave lunar orbit would have stranded the crew — which is part of why Apollo 13\'s LM engine became so critical when the SM was damaged.',
  },
  {
    id: 'rcs',
    terms: ['Reaction Control System', 'RCS'],
    short: 'Small thrusters used for fine steering, not big burns.',
    long: 'Clusters of small thrusters (on both the CSM and the LM) used for attitude control — pointing the spacecraft — and small translation moves like final approach during docking. Unlike the SPS or the LM\'s main engines, RCS thrusters fire in short, precise bursts.',
  },
  {
    id: 'agc',
    terms: ['Apollo Guidance Computer', 'AGC', 'DSKY'],
    short: 'The onboard computer — and its keypad/display unit, the DSKY.',
    long: 'A computer flown in both the CM and the LM, remarkably small and primitive by modern standards (about 2K of RAM) but revolutionary for 1966: it was among the first uses of integrated circuits in a flight-critical system. Astronauts talked to it through the DSKY ("disky," Display and Keyboard) by punching in two-digit Verb and Noun codes — you\'ll hear crews read these off constantly ("Verb 37, Noun 63...").',
    links: [{ label: 'Wikipedia: Apollo Guidance Computer', url: 'https://en.wikipedia.org/wiki/Apollo_Guidance_Computer' }],
  },
  {
    id: 'tli',
    terms: ['Translunar Injection', 'TLI'],
    short: 'The burn that leaves Earth orbit and sends the spacecraft toward the Moon.',
    long: 'After one or two laps in a low "parking" orbit to check the spacecraft out, the S-IVB third stage reignites for one long burn — Translunar Injection — that raises the trajectory\'s apogee out past the Moon. From this point the spacecraft is coasting, unpowered, for the roughly three-day trip out.',
  },
  {
    id: 'loi',
    terms: ['Lunar Orbit Insertion', 'LOI'],
    short: 'The burn that slows the spacecraft into orbit around the Moon.',
    long: 'A critical SPS burn performed behind the Moon, out of radio contact with Earth — Mission Control (and everyone listening at home) simply had to wait for the spacecraft to reappear and call home on schedule to know it worked. It slows the CSM enough for the Moon\'s gravity to capture it into orbit.',
  },
  {
    id: 'doi',
    terms: ['Descent Orbit Insertion', 'DOI'],
    short: 'A burn that lowers the LM\'s orbit to set up the final approach.',
    long: 'Performed by the LM (or, on some missions, the docked CSM/LM stack) to drop the low point of the orbit down to around 50,000 feet, setting up the trajectory for Powered Descent Initiation.',
  },
  {
    id: 'pdi',
    terms: ['Powered Descent Initiation', 'PDI'],
    short: 'The start of the actual landing burn.',
    long: 'The moment the LM\'s descent engine ignites for the final, roughly 12-minute powered descent to the surface — throttling, pitching over so the crew can see the landing site, and (on more than one mission) dealing with computer alarms or terrain that didn\'t match the plan, right up to touchdown.',
  },
  {
    id: 'tei',
    terms: ['Trans-Earth Injection', 'Trans Earth Injection', 'TEI'],
    short: 'The burn that leaves lunar orbit and heads home.',
    long: 'The SPS burn — again performed out of contact behind the Moon — that raises the CSM\'s trajectory out of lunar orbit and onto a path back to Earth. Like LOI, everyone on the ground just had to wait for the spacecraft to come back around and confirm it worked.',
  },
  {
    id: 'aos-los',
    terms: ['Acquisition of Signal', 'Loss of Signal', 'AOS', 'LOS'],
    short: 'When radio contact starts (AOS) or stops (LOS), often behind the Moon.',
    long: 'The spacecraft loses radio contact with Earth every time it passes behind the Moon (Loss of Signal) and regains it on the other side (Acquisition of Signal). Mission Control timed these to the second — an LOI or TEI burn landing right on its predicted AOS time was a strong signal that everything had gone to plan.',
  },
  {
    id: 'comm-break',
    terms: ['Comm Break'],
    short: 'A gap in the transcript where nothing significant was said.',
    long: 'A label the journal editors use for stretches of routine or unintelligible chatter that weren\'t transcribed in full — not necessarily a loss of signal, just a quiet patch.',
  },
  {
    id: 'capcom',
    terms: ['CAPCOM', 'Capsule Communicator'],
    short: 'The one person in Mission Control who talks directly to the crew.',
    long: 'By long-standing convention, only one voice — the CAPCOM, always an astronaut — spoke directly to the crew over the radio, relaying whatever the rest of Mission Control needed said. The idea was to keep the crew\'s radio loop clean and speak to them in a fellow pilot\'s voice.',
  },
  {
    id: 'eecom',
    terms: ['EECOM'],
    short: 'The Mission Control station tracking the spacecraft\'s electrical and life-support systems.',
    long: 'Short for "Electrical, Environmental and Consumables Manager" — the flight controller responsible for the CSM\'s power, oxygen, and cooling systems. EECOM John Aaron became famous for the "SCE to Aux" call on Apollo 12 after the launch lightning strikes, recognizing a garbled telemetry pattern from a simulation he\'d seen a year earlier.',
    quote: {
      text: '"So I did aid the technicians at KSC to get the spacecraft reconfigured such that they were back in a safe condition... But I drove home that night, thinking where did those squirrelly numbers come from... never thinking that when lightning struck the vehicle on Apollo 12, that exact pattern showed up. So it wasn\'t that I understood exactly what had happened, I recognized a pattern and how to get out of it."',
      attribution: 'John Aaron, 2000 oral history interview',
    },
  },
  {
    id: 'pao',
    terms: ['Public Affairs Officer', 'PAO'],
    short: 'The Mission Control voice narrating events for the public and press.',
    long: 'A separate announcer, not part of the crew\'s radio loop, who narrated milestones and status for the news media and public listening in — the "Mission Control" channel in this archive.',
  },
  {
    id: 'high-gain-antenna',
    terms: ['High-Gain Antenna', 'High Gain Antenna', 'Omni Antenna', 'Omnidirectional Antenna'],
    short: 'The steerable dish (vs. the simple always-on antennas) used for long-range or TV communication.',
    long: 'Spacecraft carried several antennas: simple "omni" antennas that radiate in most directions but have limited range, and a steerable high-gain antenna that had to be aimed at Earth for strong signal — necessary for the best voice quality and especially for TV transmissions across translunar distance.',
  },
  {
    id: 'barbecue-roll',
    terms: ['Passive Thermal Control', 'Barbecue Roll', 'PTC'],
    short: 'A slow, continuous roll during the coast phases to even out sun exposure.',
    long: 'With no atmosphere to carry away heat, one side of the spacecraft baking in direct sunlight for hours could overheat while the shaded side got dangerously cold. The fix was to put the whole stack into a slow rotisserie-like roll (about one revolution every 20 minutes) so every side got even sun exposure — hence "barbecue roll," the crews\' own nickname for it.',
  },
  {
    id: 'contingency-sample',
    terms: ['Contingency Sample'],
    short: 'A quick scoop of lunar soil taken immediately after the first steps, just in case.',
    long: 'The very first thing a commander did on the surface, before any other surface work, was scoop a small sample of soil and rock into a bag on their suit leg — insurance against an emergency that cut a moonwalk short, so the mission would come home with at least some lunar material no matter what.',
  },
  {
    id: 'core-tube',
    terms: ['Core Tube', 'Core Sample'],
    short: 'A hollow tube hammered or drilled into the ground to sample layered soil.',
    long: 'A section of pipe driven into the lunar regolith and extracted to bring back an undisturbed vertical column of soil — letting geologists read the layering, like a core sample from Earth ice or sediment, instead of just loose surface scoops.',
  },
  {
    id: 'rille',
    terms: ['Rille'],
    short: 'A long, narrow, canyon-like channel on the lunar surface.',
    long: 'A sinuous trench cut into the Moon\'s surface, thought to be a collapsed lava tube or ancient lava channel — Hadley Rille, which Apollo 15 explored by rover, is the best-known example, roughly a mile wide and 1,200 feet deep.',
  },
  {
    id: 'terminator',
    terms: ['Terminator'],
    short: 'The line between lunar day and lunar night.',
    long: 'The boundary on the Moon\'s surface (or Earth\'s, in orbital descriptions) between the sunlit side and the side in darkness — crews frequently describe watching it, since low sun angle near the terminator makes surface terrain and shadows much easier to see.',
  },
  {
    id: 'star-sighting',
    terms: ['Star Sighting', 'P52', 'Platform Alignment'],
    short: 'Sighting known stars through a sextant to check and correct the guidance platform.',
    long: 'The AGC\'s inertial platform could drift slightly over time, so crews periodically sighted pairs of known stars through an onboard sextant (a computer program numbered P52 walked them through it) to measure and correct that drift — essentially a manual GPS fix using the stars, a skill going back to ocean navigation.',
  },
  {
    id: 'plss',
    terms: ['PLSS', 'Portable Life Support System'],
    short: 'The backpack that kept a moonwalking astronaut alive.',
    long: 'The white backpack worn during EVAs, supplying oxygen, cooling water, and removing carbon dioxide and humidity — essentially a self-contained life-support system, since the suit had no hose connecting it to anything else while walking on the surface.',
  },
]

// Longest-match-first so multi-word phrases win over a shorter term they
// contain (e.g. "High-Gain Antenna" before "Omni Antenna" doesn't matter,
// but this still protects any future overlapping additions).
const allTerms = glossary
  .flatMap((entry) => entry.terms.map((t) => ({ term: t, entry })))
  .sort((a, b) => b.term.length - a.term.length)

function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export const glossaryMatchRegex = new RegExp(
  `\\b(${allTerms.map((t) => escapeRegExp(t.term)).join('|')})\\b`,
  'g',
)

const termToEntry = new Map(allTerms.map((t) => [t.term.toLowerCase(), t.entry]))

export function findGlossaryEntry(matchedText) {
  return termToEntry.get(matchedText.toLowerCase())
}
