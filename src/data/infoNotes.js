// Short explanations for numbers and jargon in the transcripts that the
// glossary doesn't cover: each rule finds a pattern in a line and explains
// what that particular phrase means. Shown as a small ⓘ after the phrase.
// Terms the glossary already explains (GET, P52, program alarms, omni
// antennas, abort modes...) are left to the glossary.

const LM_LANDING = 'In the Lunar Module, programs 63 to 68 fly the landing: P63 the braking phase, P64 the approach (the commander can see the landing site), P66 the final descent with the commander controlling the rate of descent, and P68 confirms touchdown.'
const CM_ENTRY = 'In the Command Module, programs 61 to 67 fly re-entry, from preparing for entry (P61) through separating from the Service Module (P62) to the final guided phase (P67).'

// Apollo Guidance Computer programs ("P" + two digits) other than P52.
const PROGRAMS = {
  '00': 'P00 ("P-zero-zero", often said "POO") is the computer idling, ready for the next program.',
  11: 'P11 monitors the climb to Earth orbit during launch.',
  12: 'P12 flies the Lunar Module\'s ascent from the Moon\'s surface into lunar orbit.',
  15: 'P15 monitors the translunar injection burn, which the Saturn rocket\'s own guidance flies, sending the spacecraft to the Moon.',
  20: 'P20 is rendezvous navigation: tracking the other spacecraft to close in on it.',
  21: 'P21 computes where the spacecraft will be over the ground at a given time.',
  22: 'P22 is landmark tracking: sighting known features on the surface below to refine the orbit.',
  23: 'P23 is navigation between Earth and Moon: sighting stars against Earth\'s or the Moon\'s horizon.',
  27: 'P27 lets Mission Control send new data straight into the spacecraft\'s computer.',
  30: 'P30 loads the numbers for an upcoming engine burn: when to fire and how much to change speed.',
  40: 'P40 flies a burn of the big Service Propulsion System engine.',
  41: 'P41 flies a burn using the small reaction control thrusters.',
  47: 'P47 monitors speed changes during a manual thruster burn.',
  51: 'P51 works out which way the guidance platform is pointing, using star sightings.',
  57: 'P57 aligns the Lunar Module\'s guidance platform while it sits on the Moon.',
  63: `P63 is the landing's braking phase, or in the Command Module the start of re-entry. ${LM_LANDING}`,
  64: `P64 is the landing's approach phase, or in the Command Module a stage of re-entry. ${LM_LANDING}`,
  66: `P66 is the landing's final descent, with the commander controlling the rate of descent, or in the Command Module a stage of re-entry. ${LM_LANDING}`,
  61: CM_ENTRY,
  62: CM_ENTRY,
  67: CM_ENTRY,
  70: 'P70 is an abort during the landing using the descent engine.',
  71: 'P71 is an abort during the landing using the ascent engine.',
}

const num = String.raw`\d[\d,]*(?:\.\d+)?`

export const INFO_RULES = [
  {
    re: new RegExp(String.raw`\b(${num}) by (${num})\b`, 'g'),
    when: /orbit|we're in|perigee|apogee|pericynthion|apocynthion|noun 44|n44/i,
    title: (m) => `${m[1]} by ${m[2]}`,
    text: (m) =>
      `The size of an orbit in nautical miles: ${m[1]} at its highest point and ${m[2]} at its lowest, measured above the surface. A nautical mile is about 1.15 miles or 1.85 km.`,
  },
  {
    re: /\b(\d{1,3}) plus (\d{2}) plus (\d{2})\b/g,
    title: (m) => `${m[1]} plus ${m[2]} plus ${m[3]}`,
    text: (m) =>
      `A mission time read out as hours plus minutes plus seconds since liftoff: ${Number(m[1])} hours, ${Number(m[2])} minutes and ${Number(m[3])} seconds.`,
  },
  {
    re: /\b(\d{1,2}) plus (\d{2})\b(?! plus)/g,
    title: (m) => `${m[1]} plus ${m[2]}`,
    text: (m) =>
      `Times were read out as groups joined by "plus". For a burn or countdown this is minutes plus seconds (${Number(m[1])} minutes ${Number(m[2])} seconds); for a time of day on the mission clock it is hours plus minutes.`,
  },
  {
    re: /\bP([0-7]\d)\b/g,
    only: (m) => m[1] in PROGRAMS,
    title: (m) => `P${m[1]}`,
    text: (m) => `A program in the Apollo Guidance Computer. ${PROGRAMS[m[1]]}`,
  },
  {
    re: /\bstars? (?:number )?(\d{1,2})(?:,? and (?:star )?(\d{1,2}))?\b/gi,
    title: (m) => m[0],
    text: (m) =>
      `Stars were called by number from the guidance computer's catalog of 37 navigation stars, numbered 01 to 45 in octal (base 8). To align the guidance platform (program P52) a crew member sighted ${m[2] ? `two stars, here ${m[1]} and ${m[2]},` : 'two stars'} through the spacecraft's optics, and the computer compared the angle it measured between them with the angle it expected; the result is the star angle difference (Noun 05). It then worked out how far the platform had drifted and corrected it by the "torquing angles".`,
  },
  {
    re: /\b(?:star angle difference|Noun 05|N ?05)\b/gi,
    title: () => 'Star angle difference (Noun 05)',
    text: () =>
      'The check on a star sighting: the angle the crew measured between two stars minus the angle the computer expected, in degrees. "Four balls one" (0.01°) or "all balls" (zero) means a near-perfect sighting.',
  },
  {
    re: /\b(?:gyro )?torquing angles?|\bNoun 93\b/gi,
    title: () => 'Torquing angles (Noun 93)',
    text: () =>
      'After a star sighting, how far the guidance platform had drifted, one angle in degrees for each axis. The computer "torqued" the platform\'s gyros by these amounts to line it back up; small numbers mean little drift since the last alignment.',
  },
  {
    re: /\b(?:(?:one|two|three|four|five|six|\d) )?balls(?: (?:one|two|three|four|five|six|seven|eight|nine|\d))?\b|\ball balls\b/gi,
    title: (m) => m[0],
    text: () =>
      'Radio slang for zeros, from the way a 0 looks: "four balls one" is 00001, and "all balls" is all zeros.',
  },
  {
    re: /\b(Navi|Dnoces|Regor)\b/g,
    title: (m) => m[1],
    text: () =>
      'One of three navigation stars named by the Apollo 1 crew as a joke on themselves: Navi is "Ivan" backwards (Gus Grissom\'s middle name), Dnoces is "second" backwards (for Ed White II) and Regor is "Roger" backwards (Roger Chaffee). The names stayed in the star catalog in their memory after the Apollo 1 fire.',
  },
  {
    re: /\b(Sirius|Canopus|Vega|Antares|Rigel|Arcturus|Deneb|Altair|Fomalhaut|Acrux|Achernar|Nunki|Menkent)\b/g,
    title: (m) => m[1],
    text: (m) =>
      `${m[1]} is a bright star, one of the 37 navigation stars in the Apollo guidance computer's catalog. The crew sighted pairs of these through the spacecraft's optics to line up the guidance platform.`,
  },
  {
    re: /\b(?:V|Verb )(\d{2})(?:,? ?(?:N|Noun )(\d{2}))?\b/g,
    title: (m) => m[0],
    text: () =>
      'Commands were keyed into the computer as a Verb (what to do, such as display or load) and a Noun (which data, such as a time or an angle), each a two-digit number.',
  },
  {
    re: /\bNoun (\d{2})\b/g,
    title: (m) => m[0],
    text: () =>
      'A Noun is a two-digit code telling the computer which data to work with, such as a time, an angle or a velocity. It is paired with a Verb saying what to do with it.',
  },
  {
    re: /\b(\d[\d,]*) feet,? down (?:at )?(\d+(?:\.\d+)?(?: 1\/2)?)/gi,
    title: (m) => m[0],
    text: (m) =>
      `A landing call-out: ${m[1]} feet above the surface, coming down at ${m[2]} feet per second.`,
  },
  {
    re: /\bresiduals?\b/gi,
    title: () => 'Residuals',
    text: () =>
      'What is left after a burn: the small leftover speed errors along each axis, in feet per second. Small residuals mean the burn came out very close to plan; the crew can trim them out with thrusters.',
  },
  {
    re: /\bfive[- ]by(?:[- ]five)?\b/gi,
    title: (m) => m[0],
    text: () =>
      'Radio shorthand: signal strength 5 out of 5 and clarity 5 out of 5, so loud and clear.',
  },
  {
    re: /\b\d[\d,.]* ?psi\b/gi,
    title: (m) => m[0],
    text: () => 'Pounds per square inch, the unit for pressures in tanks, suits and the cabin.',
  },
  {
    re: /\b(fps|feet per second)\b/gi,
    title: (m) => m[0],
    text: () => 'Speed in feet per second. 100 feet per second is about 68 miles per hour or 110 km/h.',
  },
  {
    re: /\b(?:delta[- ]?v|ΔV)\b/gi,
    title: () => 'Delta-V',
    text: () =>
      'Change in velocity: how much a burn speeds up or slows down the spacecraft, usually given in feet per second.',
  },
]

// Non-overlapping matches in a line: [{start, end, note: {title, text}}]
export function findInfoNotes(text) {
  const found = []
  for (const rule of INFO_RULES) {
    if (rule.when && !rule.when.test(text)) continue
    const re = new RegExp(rule.re.source, rule.re.flags)
    let m
    while ((m = re.exec(text))) {
      if (rule.only && !rule.only(m)) continue
      const start = m.index
      const end = start + m[0].length
      if (found.some((f) => start < f.end && end > f.start)) continue
      found.push({ start, end, note: { title: rule.title(m), text: rule.text(m) } })
    }
  }
  return found.sort((a, b) => a.start - b.start)
}
