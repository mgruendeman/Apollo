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
    deepDive: true,
    deepDiveText: [
      'The Command and Service Module was Apollo\'s mothership — built by North American Aviation, it was the only part of the stack designed to survive reentry, so it was the only part that ever came home. The cone-shaped Command Module (CM) held the crew for launch, the trip to and from the Moon, and reentry; the cylindrical Service Module (SM) behind it, unpressurized and jettisoned just before reentry, carried the main engine, fuel cells, and most of the consumables.',
      'Inside, the CM was cramped by any standard — roughly as much habitable volume as a large car\'s interior, shared by three astronauts and their couches for a week or more — but it packed in the guidance computer, a sextant for star sightings, food and water systems, and the parachutes and heat shield that had to work perfectly at the end of every flight, with no second chance. The Block II version flown on all crewed lunar missions added the docking tunnel and hatch that let it link up with the Lunar Module.',
      'The SPS engine in the Service Module handled every major burn beyond what the Saturn V provided — lunar orbit insertion, the return burn out of lunar orbit, and course corrections — and had no backup. That single point of failure is part of why Apollo 13\'s damaged Service Module was so dangerous: with the SPS unusable, the crew depended entirely on the Lunar Module\'s engine to get home instead.',
    ],
    images: [
      {
        src: 'glossary/csm/cm-diagram.jpg',
        caption: 'NASA cutaway illustration of the Apollo Command Module\'s interior — crew couches, instrument panels, and the heat shield around it all.',
        credit: 'NASA / Marshall Space Flight Center, illustrated by Rosemary A. Dobbins',
        sourceUrl: 'https://commons.wikimedia.org/wiki/File:Command_Module_diagram.jpg',
      },
      {
        src: 'glossary/csm/columbia-museum.jpg',
        caption: 'Apollo 11\'s Command Module Columbia — the only part of that mission\'s spacecraft to return to Earth — on display at the Smithsonian National Air and Space Museum.',
        credit: 'Alan Wilson, CC BY-SA 2.0',
        sourceUrl: 'https://commons.wikimedia.org/wiki/File:Apollo_11_Command_Service_Module_%E2%80%9CColumbia%E2%80%9D_(CSM107)_(51102281155).jpg',
      },
    ],
  },
  {
    id: 'lm',
    terms: ['Lunar Module', 'LM', 'LEM'],
    short: 'The two-person lander that actually touched down on the Moon.',
    long: 'The Lunar Module was a dedicated, ungainly-looking spacecraft built only to fly from lunar orbit to the surface and back — it never touched Earth and was never designed to fly through an atmosphere. It had two stages: a descent stage with landing legs and the main landing engine, left behind on the Moon as a launch platform, and an ascent stage carrying the crew cabin, which lifted the two moonwalkers back into lunar orbit to redock with the CSM. Early in the program it was called the Lunar Excursion Module (LEM); NASA dropped "Excursion" from the official name but the old acronym stuck around in speech.',
    links: [{ label: 'Wikipedia: Lunar module', url: 'https://en.wikipedia.org/wiki/Lunar_module' }],
    deepDive: true,
    deepDiveText: [
      'Grumman built the Lunar Module to do one job no other Apollo hardware could: land two people on the Moon and get them back into lunar orbit. Because it never had to fly through an atmosphere or survive a launch abort, its designers dropped any requirement for aerodynamics or structural toughness it didn\'t need — the result looked ungainly, with thin gold-foil-wrapped walls, spindly legs, and small triangular windows, but at roughly 33,000 pounds fully fueled for the early landings it was dramatically lighter than it otherwise would have needed to be.',
      'Its two stages worked, and separated, independently. The descent stage carried the throttleable descent engine, four landing legs, and most of the surface equipment, and stayed behind permanently as a launch platform. The ascent stage held the crew cabin, a fixed-thrust ascent engine, and its own guidance system, and was built so it could fire even if most of the rest of the LM had failed — pyrotechnic bolts and cable cutters could separate it from the descent stage in under a second if needed.',
      'Ten Lunar Modules flew in space (an eleventh, LM-2, was used only for uncrewed ground testing); six landed on the Moon. LM-7, Apollo 13\'s Aquarius, never landed at all but became the crew\'s lifeboat after the CSM was crippled — its descent engine provided the burns to get the crew home, and its systems were stretched to support three astronauts for four days instead of the two it was designed for during a landing stay.',
    ],
    images: [
      {
        src: 'glossary/lm/lm-diagram.jpg',
        caption: 'Diagram of the Apollo Lunar Module, showing the ascent stage (crew cabin, ascent engine) stacked on the descent stage (landing legs, descent engine).',
        credit: 'NASA, diagram by Magnus Manske from NASA source imagery',
        sourceUrl: 'https://commons.wikimedia.org/wiki/File:Lunar_Module_diagram.jpg',
      },
      {
        src: 'glossary/lm/eagle-lunar-orbit.jpg',
        caption: 'The Lunar Module Eagle in landing configuration, photographed from the Command Module Columbia in lunar orbit, July 20, 1969.',
        credit: 'NASA',
        sourceUrl: 'https://commons.wikimedia.org/wiki/File:Apollo_11_Lunar_Module_Eagle_in_landing_configuration_in_lunar_orbit_from_the_Command_and_Service_Module_Columbia.jpg',
      },
    ],
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
    deepDive: true,
    deepDiveText: [
      'Starting with Apollo 12, every landing crew after the first carried a science kit meant to keep working long after they\'d left: a central station with its own radio transmitter, and a set of instruments cabled out from it across the surface, all powered by a SNAP-27 radioisotope thermoelectric generator — a plutonium-238 pellet whose steady decay heat was converted to a trickle of electricity, since solar panels couldn\'t survive the two-week lunar night. Apollo 11\'s much smaller version, without the RTG, was called EASEP and ran for only about three weeks.',
      'The instrument set changed from mission to mission, but usually included a passive seismometer to record moonquakes and meteorite impacts, a magnetometer, and a solar wind detector, deployed a short walk from the lander so the lander\'s own liftoff — and the astronauts\' footsteps — wouldn\'t swamp the readings. Several ALSEP stations kept transmitting for years; the network was still returning usable science when NASA finally switched the stations off in 1977, mainly to save the cost of staffing the ground stations that monitored them.',
      'The data changed what was known about the Moon\'s interior: ALSEP seismometers recorded thousands of moonquakes and meteorite strikes, later yielded, when reanalyzed decades on, evidence that the Moon has a small, partly molten core, and — fittingly — recorded the impacts when spent S-IVB stages and LM ascent stages were deliberately crashed into the surface, calibration events planned specifically to give the seismic network something of known size and location to measure.',
    ],
    images: [
      {
        src: 'glossary/alsep/alsep-deploy.jpg',
        caption: 'Apollo 12\'s Alan Bean works beside the Lunar Module with the two ALSEP packages unloaded onto the surface, ready to be carried out for deployment, November 1969.',
        credit: 'NASA (AS12-46-6792)',
        sourceUrl: 'https://commons.wikimedia.org/wiki/File:ALSEP_AS12-46-6792.jpg',
      },
    ],
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
    deepDive: true,
    deepDiveText: [
      'The Apollo Guidance Computer, built by the MIT Instrumentation Laboratory and manufactured by Raytheon, was one of the first computers built around integrated circuits rather than individual transistors — a choice driven purely by weight and space, since ICs let MIT fit real computing power into a box the size of a small suitcase. Both the CM and the LM carried one; each had 36,864 sixteen-bit words (about 72 KB) of fixed "rope" memory — program instructions physically woven into the hardware — plus 2,048 words (about 4 KB) of erasable memory for live calculations.',
      'Astronauts talked to it through the DSKY (Display and Keyboard, pronounced "disky") by entering two-digit Verb and Noun codes — Verb told the computer what action to take, Noun told it what to take that action on. "Verb 37 Noun 63," for instance, called up a display and loaded a new major program. It\'s a terse, transcript-filling shorthand that shows up constantly once a crew is deep into a burn or a landing sequence.',
      'The AGC\'s most famous moment came during Apollo 11\'s landing, when a checklist mismatch left the rendezvous radar powered on, flooding the computer with more interrupts than expected and triggering a string of 1202 and 1201 program alarms. Rather than crash, the software — designed by MIT\'s team, with Margaret Hamilton leading the flight software effort, to shed lower-priority work and restart when overloaded — kept the essential landing functions running, and in Mission Control the guidance team, who had drawn up a list of which alarms were safe to fly through after a training simulation, gave the crew a "go" to continue.',
    ],
    images: [
      {
        src: 'glossary/agc/dsky.jpg',
        caption: 'An Apollo Guidance Computer Display and Keyboard (DSKY) unit removed from the Command Module simulator at Johnson Space Center — the same interface astronauts trained and flew with.',
        credit: 'Steve Jurvetson, CC BY 2.0',
        sourceUrl: 'https://commons.wikimedia.org/wiki/File:Apollo_DSKY_from_CM_Simulator_(6378253427).jpg',
      },
    ],
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
    deepDive: true,
    deepDiveText: [
      'EECOM stood for Electrical, Environmental and Consumables Manager (in Mercury-era usage, Electrical, Environmental and Communications) — the flight controller who owned the CSM\'s power, oxygen, water, and cabin systems. It\'s a role best remembered for two very different nights nine months apart: John Aaron\'s "SCE to AUX" call that saved Apollo 12 after a lightning strike during launch, and Sy Liebergot\'s watch on console during Apollo 13\'s oxygen tank explosion.',
      'On the night of April 13, 1970, Liebergot was the EECOM on duty when a routine cryogenic tank stir set off damaged wiring inside oxygen tank 2, rupturing it and damaging tank 1 alongside it. His instruments showed readings that didn\'t make physical sense — pressures crashing, voltages dropping across systems that shouldn\'t have been connected — and for a few critical minutes the data looked enough like an instrumentation glitch that even Liebergot wondered aloud if it was one, before the evidence of a real, spreading failure became unmistakable.',
      'What followed was less a single dramatic call than days of methodical work by EECOM and every other console, under Flight Director Gene Kranz and the other flight directors, to figure out how to keep three men alive on a crippled spacecraft: powering down the CSM to conserve its last reserves, moving the crew into the Lunar Module as a lifeboat it was never designed to be, and improvising a fix for carbon dioxide scrubbers that didn\'t fit the LM\'s canisters. It\'s the flight-controller story the Apollo program is most remembered for, and it happened almost entirely off the radio loop the public was listening to.',
    ],
    images: [
      {
        src: 'glossary/eecom/mocr-apollo13.jpg',
        caption: 'The Mission Operations Control Room during Apollo 13\'s television broadcast on the evening of April 13, 1970, with the crew on the big screen — shortly before the oxygen tank explosion.',
        credit: 'NASA (S70-35136)',
        sourceUrl: 'https://commons.wikimedia.org/wiki/File:Mission_Operations_Control_Room_during_Apollo_13.jpg',
      },
    ],
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
    deepDive: true,
    deepDiveText: [
      'The Portable Life Support System was, in effect, a wearable spacecraft: with the suit sealed, it was the only thing standing between an astronaut and vacuum, radiation, and temperatures that swung from over 200°F in sunlight to far below freezing in shadow. Worn on the back like an oversized rucksack, it weighed about 84 pounds on Earth (a fraction of that in lunar gravity) and supplied oxygen, removed exhaled carbon dioxide with a lithium hydroxide canister, and circulated cooling water through a mesh undergarment worn against the skin.',
      'Later missions extended what the PLSS could do. From Apollo 15 on, larger consumables stretched EVA time to around seven hours per moonwalk, up from about four hours on the first landing missions. The PLSS radio talked to the LM (or, on the rover missions, to the rover\'s relay unit), which relayed voice on to Houston. Strapped on top of the PLSS itself was the separate OPS, a pair of high-pressure bottles good for about 30 minutes of emergency oxygen if the PLSS failed outright.',
      'Every gram on the backpack mattered, and every failure mode had to be survivable without ever getting back inside — there was no repair kit for a cracked oxygen line a mile from the LM. The PLSS is one reason moonwalks were planned so conservatively: consumables, not curiosity, usually set the limit on how far a crew could wander before they had to turn back.',
    ],
    images: [
      {
        src: 'glossary/plss/aldrin-plss.jpg',
        caption: 'Buzz Aldrin on the lunar surface during Apollo 11, wearing the PLSS backpack; Neil Armstrong and the Lunar Module Eagle are reflected in his helmet visor.',
        credit: 'NASA / Neil Armstrong (AS11-40-5903)',
        sourceUrl: 'https://commons.wikimedia.org/wiki/File:AS11-40-5903_-_Buzz_Aldrin_by_Neil_Armstrong_(full_frame).jpg',
      },
    ],
  },

  // -- Saturn V (deep dive) --------------------------------------------
  {
    id: 'saturn-v',
    terms: ['Saturn V'],
    short: 'The three-stage rocket that launched every Apollo mission — still the most powerful ever flown to orbit.',
    long: 'Standing 363 feet tall — taller than the Statue of Liberty — the Saturn V was NASA\'s answer to one brutal requirement: throw about 100,000 pounds of spacecraft out of Earth orbit and onto a course for the Moon. It flew in three stages, each one burning out, separating, and dropping away in turn, so the vehicle got lighter (and its engines more efficient for vacuum) as it climbed. Thirteen Saturn Vs flew, and none ever lost its payload.',
    deepDive: true,
    deepDiveText: [
      'The Saturn V flew in three stages, each a separate rocket stacked and staged in sequence. The S-IC first stage, built by Boeing, burned RP-1 kerosene and liquid oxygen through five F-1 engines for about two and a half minutes, producing 7.5 million pounds of thrust at liftoff. The S-II second stage, from North American Aviation, picked up the climb with five J-2 engines burning liquid hydrogen, and the single-engine S-IVB third stage, built by Douglas, finished the job — first with a short burn into a low Earth "parking" orbit, then, after the crew checked the spacecraft out, a longer Translunar Injection burn that sent it toward the Moon.',
      'Fully fueled, the rocket weighed about 6.2 million pounds, nearly all of it propellant. Only a tiny fraction of that mass — the Command Module — ever made it home; the rest was shed in pieces along the way. The first two stages fell into the ocean, and the third stage was either sent into solar orbit or, from Apollo 13 onward, deliberately crashed into the Moon to register on the seismometers earlier crews had just set up.',
      'The Saturn V\'s design was overseen by Wernher von Braun\'s team at the Marshall Space Flight Center, building on the earlier Saturn I family. It flew thirteen times between 1967 and 1973 — the uncrewed Apollo 4 and 6 test flights, the ten crewed flights from Apollo 8 through Apollo 17 (including Apollo 9, which stayed in Earth orbit), and the launch of the Skylab space station — without ever losing a payload, though Apollo 6 and Apollo 13 each lost engines early and had to burn the remaining ones longer to compensate.',
    ],
    images: [
      {
        src: 'glossary/saturn-v/saturn-v-schematic.jpg',
        caption: 'NASA schematic of the Saturn V launch vehicle, showing its three stages, the instrument unit, and the Apollo spacecraft on top.',
        credit: 'NASA / Marshall Space Flight Center',
        sourceUrl: 'https://commons.wikimedia.org/wiki/File:Saturn_v_schematic.jpg',
      },
      {
        src: 'glossary/saturn-v/apollo-11-liftoff.jpg',
        caption: 'The Apollo 11 Saturn V lifts off from Pad 39A at Kennedy Space Center, July 16, 1969.',
        credit: 'NASA (KSC-69PC-442)',
        sourceUrl: 'https://commons.wikimedia.org/wiki/File:Apollo_11_Saturn_V_lifting_off_on_July_16,_1969.jpg',
      },
    ],
  },
  {
    id: 's-ic',
    terms: ['S-IC'],
    short: 'The Saturn V\'s first stage — five F-1 engines, gone two and a half minutes after liftoff.',
    long: 'The S-IC was the Saturn V\'s giant first stage, 138 feet tall and burning RP-1 kerosene and liquid oxygen through five F-1 engines for about two and a half minutes — long enough to get the stack up to roughly 40 miles and 6,000 mph before it separated and fell into the Atlantic. Built by Boeing, it produced the bulk of the rocket\'s liftoff thrust, 7.5 million pounds combined, before the stack ever cleared the thickest part of the atmosphere.',
  },
  {
    id: 's-ii',
    terms: ['S-II'],
    short: 'The Saturn V\'s second stage — five J-2 engines burning liquid hydrogen.',
    long: 'Built by North American Aviation, the S-II picked up where the S-IC left off, burning liquid hydrogen and liquid oxygen through five J-2 engines for about six minutes to carry the stack most of the way to orbital velocity. To save weight, its hydrogen and oxygen tanks shared a single insulated common bulkhead instead of two separate tank walls.',
  },
  {
    id: 's-ivb',
    terms: ['S-IVB'],
    short: 'The Saturn V\'s third stage — did double duty: parking orbit, then the burn to the Moon.',
    long: 'The S-IVB carried a single restartable J-2 engine and fired twice: first for a roughly two-minute burn that placed the stack into low Earth "parking" orbit, and then again, after a coast to check everything out, for the several-minute Translunar Injection burn that sent the spacecraft toward the Moon. That in-flight restart capability is what let one stage do both jobs.',
  },
  {
    id: 'les',
    terms: ['Launch Escape System', 'Launch Escape Tower'],
    short: 'The rocket tower atop the Command Module, there to pull the crew clear of a failing booster.',
    long: 'A slim tower of solid-fuel motors mounted above the Command Module, the Launch Escape System existed for one purpose: if the Saturn V failed on the pad or in the first few minutes of flight, its escape motor could pull the CM — and crew — safely away and clear for a parachute landing. It was jettisoned in a routine burn of its own once the vehicle was safely past the point where it was still needed, a moment crews called out over the radio.',
  },
  {
    id: 'f1-engine',
    terms: ['F-1 engine', 'F-1'],
    short: 'The engine that powered the Saturn V\'s first stage — still the most powerful single-chamber rocket engine ever flown.',
    long: 'Five F-1 engines, burning RP-1 kerosene and liquid oxygen, powered the S-IC first stage, each one producing about 1.5 million pounds of thrust — 7.5 million pounds combined at liftoff. Built by Rocketdyne, the F-1 remains, decades later, the most powerful single-combustion-chamber liquid-fuel rocket engine ever flown.',
  },
  {
    id: 'j2-engine',
    terms: ['J-2 engine', 'J-2'],
    short: 'The high-efficiency hydrogen engine used on the Saturn V\'s upper two stages.',
    long: 'The J-2, also built by Rocketdyne, burned liquid hydrogen and liquid oxygen and flew in clusters of five on the S-II second stage and singly on the S-IVB third stage. Unlike the F-1, it was designed to be shut down and restarted in flight — a capability the S-IVB relied on to fire once for orbit insertion and again, later in the same mission, for Translunar Injection.',
  },

  // -- Flight controller roles ------------------------------------------
  {
    id: 'fido',
    terms: ['Flight Dynamics Officer', 'FIDO'],
    short: 'The Mission Control station that owns the spacecraft\'s trajectory.',
    long: 'Short for Flight Dynamics Officer, FIDO sat in the front row of Mission Control and was responsible for the spacecraft\'s trajectory end to end — launch monitoring, orbit determination, burn targeting, and the go/no-go calls tied to where the vehicle actually was and where it was headed. FIDO worked hand in hand with GUIDO, the console immediately alongside, cross-checking the onboard guidance against ground tracking.',
  },
  {
    id: 'guido',
    terms: ['Guidance Officer', 'GUIDO'],
    short: 'Mission Control\'s watchdog on the spacecraft\'s onboard guidance and navigation.',
    long: 'The Guidance Officer, called GUIDO over the loop, monitored the onboard guidance computer and inertial platform against Mission Control\'s own trajectory data, flagging any divergence between what the spacecraft thought it was doing and what the ground could see. GUIDO Steve Bales became well known for the split-second call to keep going through Apollo 11\'s 1202 and 1201 program alarms during the landing, backed by his support team\'s read of exactly what those alarms meant.',
  },
  {
    id: 'gnc',
    terms: ['Guidance, Navigation and Control Officer', 'GNC'],
    short: 'The console watching the spacecraft\'s guidance hardware itself — engines, gyros, thrusters.',
    long: 'GNC (Guidance, Navigation and Control) was the systems engineer responsible for the hardware side of guidance and control — the CSM\'s or LM\'s actual gyros, thrusters, and engine gimbal drives — as distinct from GUIDO, who watched the software and navigation solution. Mission Control ran separate CSM GNC and LM GNC consoles side by side once a mission included a Lunar Module, since each vehicle\'s control hardware needed its own eyes.',
  },
  {
    id: 'telmu',
    terms: ['TELMU'],
    short: 'The LM\'s life-support and electrical console — EECOM\'s counterpart for the lander.',
    long: 'TELMU (Telemetry, Electrical, and EVA Mobility Unit Officer) tracked the Lunar Module\'s electrical power and environmental control systems, plus the spacesuits once the crew was outside on the surface — essentially doing for the LM and its moonwalkers what EECOM did for the CSM.',
  },
  {
    id: 'control',
    terms: ['CONTROL'],
    short: 'The Mission Control console for the Lunar Module\'s guidance and navigation hardware.',
    long: 'CONTROL was the LM-side counterpart to the CSM\'s GNC console, watching the Lunar Module\'s guidance, navigation, and control hardware — its inertial platform, thrusters, and descent and ascent engine controls — through the phases when the LM\'s own systems mattered most.',
  },
  {
    id: 'retro',
    terms: ['Retrofire Officer', 'RETRO'],
    short: 'The console responsible for reentry and abort trajectories.',
    long: 'RETRO, short for Retrofire Officer, calculated and monitored the burns needed to bring the crew home safely — nominal reentry targeting as well as the retrograde burns tied to every abort mode off the pad or during ascent. The role dated back to Mercury and Gemini, where "retrofire" literally meant firing retro-rockets to drop out of orbit.',
  },
  {
    id: 'flight-director',
    terms: ['Flight Director'],
    short: 'The person in charge of a shift in Mission Control — call sign "Flight."',
    long: 'The Flight Director ran the room: every controller\'s console fed information up to Flight, and every major decision — a go/no-go, an abort call, a change of plan — was theirs to make and theirs alone to answer for. Gene Kranz, Flight Director for Apollo 11\'s landing and Apollo 13\'s rescue, is remembered for the "Tough and Competent" speech he gave after the Apollo 1 fire, telling every controller to write those two words on their blackboard and never erase them.',
    quote: {
      text: '"Spaceflight will never tolerate carelessness, incapacity, and neglect... Tough means we are forever accountable for what we do or what we fail to do. We will never again compromise our responsibilities. Competent means we will never take anything for granted."',
      attribution: 'Gene Kranz, address to Mission Control staff, January 1967, after the Apollo 1 fire',
    },
  },
  {
    id: 'inco',
    terms: ['Instrumentation and Communications Officer', 'INCO'],
    short: 'The console responsible for the spacecraft\'s onboard communications and telemetry equipment.',
    long: 'INCO monitored and commanded the spacecraft\'s communications and data systems — antennas, transponders, telemetry formatting — troubleshooting the hardware that got voice, tracking, and data to and from the ground, as distinct from the network controllers who ran the ground stations themselves.',
  },
  {
    id: 'surgeon',
    terms: ['SURGEON', 'Flight Surgeon'],
    short: 'The flight controller monitoring the crew\'s health and biomedical data.',
    long: 'The flight surgeon\'s console, call sign SURGEON, watched real-time biomedical telemetry — heart rate, respiration — piped down from sensors in the crew\'s suits, advising the Flight Director on anything medical, from a crew member\'s sleep and workload to their fitness to continue.',
  },

  // -- LM / CSM subsystems ------------------------------------------------
  {
    id: 'ascent-stage',
    terms: ['Ascent Stage'],
    short: 'The half of the LM that carried the crew back off the Moon.',
    long: 'The upper half of the Lunar Module, holding the pressurized crew cabin, the ascent engine, and the guidance systems, the ascent stage was what actually lifted off the surface at the end of a moonwalk — using the descent stage\'s landing legs as a launch pad and leaving it behind. It had no backup engine; a failure of the single ascent engine to fire would have stranded the crew on the surface.',
  },
  {
    id: 'descent-stage',
    terms: ['Descent Stage'],
    short: 'The lower half of the LM — landing legs, main engine, and everything left behind on the Moon.',
    long: 'The descent stage carried the throttleable landing engine, the four landing legs, and most of the surface gear — tools, the ALSEP, sample containers — everything needed to get down safely and support a stay on the surface. It stayed on the Moon permanently, serving as the launch platform the ascent stage fired from when the crew left.',
  },
  {
    id: 'docking-probe',
    terms: ['Docking Probe', 'Probe and Drogue'],
    short: 'The retractable spike-and-cone mechanism that linked the CSM and LM nose to nose.',
    long: 'Docking used a probe, mounted in the CSM\'s nose, that speared into a cone-shaped drogue on the LM\'s docking tunnel. Three latches on the probe gave a "soft dock" on first contact; the CMP then retracted the probe electrically, drawing the two craft together until twelve latches around the rim clamped down for an airtight "hard dock." The probe-and-drogue assembly could then be unbolted and stowed to let the crew crawl through the tunnel.',
  },
  {
    id: 'emu',
    terms: ['Extravehicular Mobility Unit', 'EMU'],
    short: 'The full spacesuit assembly worn on the surface — distinct from the PLSS backpack alone.',
    long: 'EMU is NASA\'s term for the entire pressure-suit system an astronaut wore on the lunar surface: the multi-layer A7L suit itself, helmet, visor assembly, and gloves, plus the PLSS backpack and its OPS emergency bottle strapped on top. "EMU" and "PLSS" get used loosely in conversation, but strictly the PLSS is only the life-support backpack — one component of the larger EMU.',
  },
  {
    id: 'ops',
    terms: ['Oxygen Purge System', 'OPS'],
    short: 'The backpack\'s emergency bailout bottle — about 30 minutes of backup oxygen.',
    long: 'Mounted on top of the PLSS, the Oxygen Purge System was a self-contained pair of high-pressure oxygen bottles that could be switched on if the PLSS itself failed, feeding the suit directly for roughly 30 minutes — long enough, by design, to get back to the LM. In a real PLSS failure, a "buddy" hose run from a working PLSS could extend that window further by taking over cooling.',
  },

  // -- Lunar Roving Vehicle (deep dive) -----------------------------------
  {
    id: 'lrv',
    terms: ['Lunar Roving Vehicle', 'LRV', 'Rover'],
    short: 'The battery-powered "Moon buggy" used on the last three landing missions.',
    long: 'A folding, four-wheeled electric car carried collapsed on the LM\'s descent stage and unpacked on the surface, the LRV let the Apollo 15, 16 and 17 crews range miles from the lander instead of walking everywhere on foot. It had wire-mesh wheels, a top speed of about 8 mph, a TV camera Houston could steer remotely, and no landing back home — all three that flew are still on the Moon.',
    deepDive: true,
    deepDiveText: [
      'Built by Boeing and Delco, the Lunar Roving Vehicle folded up small enough to ride out to the Moon strapped to the side of the LM\'s descent stage, then unfolded — largely under spring tension, needing only a light pull from the crew — into a two-seat, four-wheel-drive electric car weighing about 460 pounds empty. Each of its four wheels had its own quarter-horsepower electric motor, powered by a pair of silver-zinc batteries, giving it a top speed of around 8 mph; traverses were planned so the crew could always walk back to the LM if the rover broke down.',
      'It rode on wire-mesh wheels rather than rubber tires — rubber would have gone brittle in the temperature swings and vacuum — with a steel chevron tread bonded on for traction, and it steered through both front and rear wheels for a tight turning circle. A color TV camera on the front, controlled remotely by an engineer back in Houston, let Mission Control watch — and sometimes help direct — the crew\'s surface activities live.',
      'Three rovers flew, one each on Apollo 15, 16 and 17, and all three are still on the Moon; there was never a plan to bring one home. Apollo 17\'s Gene Cernan reported hitting about 11 mph on a downhill run, still the fastest anyone has driven on the Moon.',
    ],
    images: [
      {
        src: 'glossary/lrv/lrv-checkout.jpg',
        caption: 'Apollo 17 commander Eugene Cernan checks out the Lunar Roving Vehicle at the start of the mission\'s first moonwalk, December 1972.',
        credit: 'NASA / Harrison H. Schmitt (AS17-147-22526)',
        sourceUrl: 'https://commons.wikimedia.org/wiki/File:NASA_Apollo_17_Lunar_Roving_Vehicle.jpg',
      },
    ],
  },

  // -- Procedures / events -------------------------------------------------
  {
    id: 'rendezvous',
    terms: ['Rendezvous'],
    short: 'The orbital meetup and re-docking of the ascent stage with the CSM.',
    long: 'Rendezvous is the general term for two spacecraft matching orbits and closing the gap between them — most critically, the LM ascent stage catching up to and redocking with the orbiting CSM after a moonwalk. NASA developed and rehearsed the techniques during Gemini specifically so Apollo crews could count on them working when their lives depended on it.',
  },
  {
    id: 'quarantine',
    terms: ['Mobile Quarantine Facility', 'Lunar Receiving Laboratory', 'Quarantine', 'MQF'],
    short: 'The 21-day medical isolation imposed on early lunar crews and their samples, just in case.',
    long: 'Out of caution that lunar material might carry something dangerous, the Apollo 11, 12 and 14 crews went straight from splashdown into the Mobile Quarantine Facility — a converted Airstream trailer — for the trip home, then into the Lunar Receiving Laboratory in Houston to finish a 21-day isolation alongside their rock samples. No lunar pathogen ever turned up, and NASA dropped the practice after Apollo 14.',
  },
  {
    id: 'splashdown',
    terms: ['Splashdown'],
    short: 'The Command Module\'s parachute landing in the ocean, ending every mission.',
    long: 'Every Apollo mission ended the same way: after separating from the Service Module, the Command Module rode its heat shield through reentry, then a sequence of drogue and main parachutes eased it down for splashdown in the Pacific Ocean — except Apollo 7 and Apollo 9, which came down in the Atlantic — where a Navy carrier and frogman swim team were standing by to recover the crew.',
  },
  {
    id: 'abort-modes',
    terms: ['Abort Mode', 'Mode I', 'Mode II', 'Mode IV'],
    short: 'The numbered plans for getting the crew home safely if the Saturn V or SPS failed.',
    long: 'Apollo abort planning defined a numbered sequence of options that shifted as a mission progressed: Mode I meant firing the Launch Escape Tower off the pad or in early flight; Mode II relied on the Command Module\'s own lift to glide to a safe splashdown once the tower was gone; Mode III added an SPS burn to steer the entry point into safer water; and Mode IV covered a failure during the S-IVB\'s burn, using the SPS to reach a safe Earth orbit instead of an immediate return. Crews and controllers tracked exactly which mode applied at every second of ascent.',
  },
  {
    id: 'gimbal-lock',
    terms: ['Gimbal Lock'],
    short: 'The orientation where the guidance platform\'s gimbals line up and it loses track of attitude.',
    long: 'The AGC\'s inertial platform was mounted on three gimbals, and engineers chose not to add a fourth to protect against the geometry where two of them align and the platform can no longer sense rotation about one axis — gimbal lock. The LM\'s computer flashed a warning at 70 degrees of gimbal angle and froze the platform outright at 85 to protect it; from there the crew had to fly clear manually and realign the platform against the stars from scratch.',
  },
  {
    id: 'program-alarm',
    terms: ['Program Alarm', '1202', '1201'],
    short: 'The AGC\'s way of flagging a computer overload — most famously "1202" and "1201" during Apollo 11\'s landing.',
    long: 'When the guidance computer\'s job queue backed up faster than it could clear, it threw a numbered program alarm and restarted its lower-priority tasks rather than crash outright — a deliberate design choice that let it keep flying even overloaded. During Apollo 11\'s final descent the crew got a string of 1202 and 1201 "executive overflow" alarms, caused by a checklist mismatch that left a radar switch in the wrong position; on the ground, back-room engineer Jack Garman, who had written up a list of every program alarm and whether it was safe to fly through after a training simulation, told Guidance Officer Steve Bales these were safe to continue on.',
    quote: {
      text: '"We\'re Go on that alarm."',
      attribution: 'Charlie Duke, CAPCOM, relaying Guidance Officer Steve Bales\'s call to the Apollo 11 crew during the lunar descent, GET 102:38:53',
    },
  },
  {
    id: 's-band',
    terms: ['S-Band', 'Unified S-Band'],
    short: 'The single radio system carrying voice, tracking, telemetry, and TV between spacecraft and Earth.',
    long: 'The Unified S-Band system combined what used to be separate radio links — voice, telemetry, tracking, and, when the antenna was aimed right, live television — onto one S-band frequency pair per spacecraft, simplifying both the onboard hardware and the ground network needed to talk to it. It\'s why a single "the signal\'s good" or "we\'ve lost S-band" from Mission Control covered so much at once.',
  },

  // -- Guidance systems ------------------------------------------------
  {
    id: 'pgns',
    terms: ['PGNS', 'Primary Guidance, Navigation and Control System', 'PGNCS'],
    short: 'The LM\'s main computer-driven guidance system — same computer family as the AGC, its own inertial platform.',
    long: 'PGNS (pronounced "pings," sometimes written PGNCS) was the Lunar Module\'s primary guidance system: an Apollo Guidance Computer, its own inertial platform, and the software that flew the descent, ascent, and rendezvous. It\'s the system a crew is referencing whenever they call out switching between "primary" and "abort" guidance.',
  },
  {
    id: 'ags',
    terms: ['Abort Guidance System', 'AGS'],
    short: 'The LM\'s independent backup computer, built to get the crew off the surface if PGNS failed.',
    long: 'A separate, simpler computer and platform built by TRW, deliberately independent of the AGC\'s design team as a hedge against a shared flaw, the Abort Guidance System could fly the LM off the surface and into a rendezvous with the CSM, but had no software for landing itself. It flew on every mission as a backup and was never actually needed to fly an abort.',
  },

  // -- Crew roles ------------------------------------------------------
  {
    id: 'cdr',
    terms: ['CDR', 'Commander'],
    short: 'The mission commander — overall responsible for the flight, and the one who flew the LM to landing.',
    long: 'The Commander (CDR) was the senior astronaut on the crew, in overall charge of the mission and specifically the one at the LM\'s hand controllers for the landing itself. The Commander was always first down the ladder; of the twelve moonwalkers, six were commanders and six were Lunar Module Pilots.',
  },
  {
    id: 'lmp',
    terms: ['LMP', 'Lunar Module Pilot'],
    short: 'The crew seat responsible for the LM\'s systems — and, on landing missions, the second moonwalker.',
    long: 'Despite the title, the Lunar Module Pilot didn\'t fly the LM during landing — the Commander did — the LMP\'s job was running the LM\'s systems, backing up navigation and computer inputs, and calling out altitude and descent-rate numbers during the approach. On the surface, the LMP was the second person out the hatch.',
  },
  {
    id: 'cmp',
    terms: ['CMP', 'Command Module Pilot'],
    short: 'The crew member who stayed in lunar orbit, flying the CSM solo while the other two landed.',
    long: 'The Command Module Pilot flew the CSM alone in lunar orbit for the one to three days the other two crew members were on the surface — running experiments, navigating, and above all keeping the ship ready to bring everyone home, including the tense job of rendezvous and redocking with the ascent stage on its way back up.',
  },

  // -- Named places / samples ------------------------------------------
  {
    id: 'cone-crater',
    terms: ['Cone Crater'],
    short: 'The rim Apollo 14\'s crew never quite reached, hunting the mission\'s prime rock target.',
    long: 'A young, sharp-walled crater above Apollo 14\'s Fra Mauro landing site, Cone Crater was the mission\'s main geology objective, since its ejecta promised deep, ancient material. Alan Shepard and Ed Mitchell spent their second moonwalk trudging uphill through confusing, cratered terrain toward it, exhausted and behind schedule, and were called back by Houston when they were — as later mapping showed — within about 100 feet of the rim without ever being sure they\'d find it.',
  },
  {
    id: 'descartes',
    terms: ['Descartes'],
    short: 'The lunar highlands Apollo 16 landed in, named for the crater (and the philosopher).',
    long: 'Apollo 16 landed in the Descartes Highlands, chosen because geologists expected volcanic material there — a hoped-for contrast to the mare basalts earlier missions had sampled. Instead John Young and Charlie Duke found the highlands were built from impact breccia, not lava, a surprise that reshaped ideas about how the Moon\'s highlands formed. Both the landing site and its namesake crater take their name from the 17th-century French philosopher and mathematician René Descartes.',
  },
  {
    id: 'taurus-littrow',
    terms: ['Taurus-Littrow'],
    short: 'The mountain-ringed valley where Apollo 17, the last landing mission, touched down.',
    long: 'Apollo 17 landed in the Taurus-Littrow valley, on the southeastern edge of Mare Serenitatis, named for the surrounding Taurus mountains and the nearby crater Littrow. Its steep valley walls and evidence of possible volcanic activity made it a prime target for the program\'s final, most geologically ambitious landing, with Harrison Schmitt aboard as the only professional geologist to walk on the Moon.',
  },
  {
    id: 'big-muley',
    terms: ['Big Muley'],
    short: 'The largest rock brought back from the Moon — 26 pounds, from Apollo 16.',
    long: 'Lunar sample 61016, nicknamed Big Muley, is the largest single rock any Apollo mission returned: an 11.7-kilogram breccia picked up by John Young and Charlie Duke at Plum Crater. It\'s named for Bill Muehlberger, the geologist who led the Apollo 16 crew\'s field geology training and mission support.',
  },
  {
    id: 'genesis-rock',
    terms: ['Genesis Rock'],
    short: 'A pale anorthosite chunk from Apollo 15, once thought to be a piece of the Moon\'s original crust.',
    long: 'Spotted perched on a small pedestal at Spur Crater, sample 15415 was a strikingly white rock that stood out from the surrounding gray regolith. Nicknamed the Genesis Rock, it was later dated at roughly 4 billion years old, though further study showed it wasn\'t quite the pristine, primordial crust sample it was first taken for.',
    quote: {
      text: 'Guess what we just found! I think we found what we came for.',
      attribution: 'David Scott, Apollo 15, August 1, 1971',
    },
  },
  {
    id: 'fra-mauro',
    terms: ['Fra Mauro'],
    short: 'The hilly highland formation Apollo 14 landed in — the site Apollo 13 never reached.',
    long: 'Named for the crater at its center (itself named for a 15th-century Italian monk and mapmaker), the Fra Mauro formation was thought to be debris thrown out by the ancient impact that formed Mare Imbrium — layers of it, sampled at Cone Crater, promised a look far back into the Moon\'s early history. It had been Apollo 13\'s landing site before that mission was aborted; Apollo 14 flew the same target about ten months later and finally got there.',
  },

  // -- Mission Control (deep dive) ---------------------------------------
  {
    id: 'mission-control',
    terms: ['Mission Control', 'MOCR', 'Mission Operations Control Room'],
    short: 'The Houston control room — and the roomful of flight controllers in it — that ran every mission in real time.',
    long: 'Formally the Mission Operations Control Room (MOCR, pronounced "moh-ker"), in Building 30 at the Manned Spacecraft Center in Houston, this was the room full of console positions — Flight, CAPCOM, FIDO, EECOM, and dozens more — that flew every Gemini and Apollo mission from the ground. Two MOCRs existed on different floors of the building; the one that ran most Apollo missions, including Apollo 11, is now preserved as a National Historic Landmark.',
    deepDive: true,
    deepDiveText: [
      'Mission Control\'s basic shape was set by Christopher Kraft, NASA\'s first flight director, during the Mercury program: one flight director with final authority, a set of specialist consoles each owning one part of the mission, and a single astronaut CAPCOM as the only voice actually talking to the crew. By Apollo, that had grown to roughly two dozen positions across four rows, from trajectory specialists like FIDO and RETRO in the front row to program managers and the public affairs officer at the back.',
      'The room in Building 30 that ran Apollo 11\'s landing — Mission Operations Control Room 2 — is the one most people picture: rows of gray consoles, wall-sized projection screens, and, since smoking was still allowed on console through the 1960s and 70s, a permanent haze. It was designated a National Historic Landmark in 1985 and fully restored, down to period ashtrays and coffee cups, in a NASA-led restoration completed in 2019 for the Apollo 11 anniversary.',
      'Every controller in the room had a backroom of specialists feeding them data and options in real time, so a single voice on the flight director\'s loop — "go" or "no-go" — represented a chain of people who\'d already checked it several ways. That structure is what let the room work through Apollo 13\'s oxygen tank explosion methodically, rather than in a panic, while three lives hung on getting every step right.',
    ],
    images: [
      {
        src: 'glossary/mission-control/mocr-apollo11.jpg',
        caption: 'Flight controllers and NASA officials celebrate in the Mission Operations Control Room at the conclusion of Apollo 11, July 24, 1969.',
        credit: 'NASA (S69-40301)',
        sourceUrl: 'https://commons.wikimedia.org/wiki/File:Mission_Operations_Control_Room_at_the_conclusion_of_Apollo_11.jpg',
      },
    ],
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
