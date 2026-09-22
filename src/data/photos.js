// NASA photographs tied to the curated `highlights` clips in missions.js,
// shown while that clip is playing. Captions note when a photo was taken
// at a different moment from the audio. All images are NASA public-domain
// works from images.nasa.gov, resized for the web.

const photos = [
  ['a08_0000000', '08/launch.jpg', 'S68-56001', 'Apollo 8 lifts off from Pad 39A at 7:51 a.m. EST, December 21, 1968 — the first crewed Saturn V.'],
  ['a08_0850219-onboard-nr', '08/earthrise.jpg', 'as08-14-2383', 'Earthrise, photographed from lunar orbit on December 24, 1968 — the same day as the crew\'s Christmas Eve broadcast.'],
  ['a10-0000254', '10/launch.jpg', '6975432', 'Apollo 10\'s Saturn V (SA-505) lifts off on May 18, 1969.'],
  ['a11_0000000', '11/launch.jpg', '6901001', 'Apollo 11\'s Saturn V (SA-506) lifts off from Launch Complex 39A, July 16, 1969.'],
  ['a11a1023540HSK', '11/eagle-on-surface.jpg', 'as11-40-5927', 'Eagle at Tranquility Base, photographed by Neil Armstrong during the moonwalk a few hours after landing, with Buzz Aldrin unpacking experiments.'],
  ['Apollo11_FD_Audio_Loop_John_Sarkissian', '11/bootprint.jpg', 'as11-40-5877', 'An astronaut\'s bootprint in the lunar soil, photographed during Apollo 11\'s moonwalk.'],
  ['a12a_000_00_00', '12/launch.jpg', '6903391', 'Apollo 12 lifts off under overcast skies on November 14, 1969; the vehicle was struck by lightning twice in its first minute.'],
  ['a12a.1151543', '12/bean-ladder.jpg', 'as12-46-6726', 'Alan Bean starts down the ladder of the Lunar Module Intrepid to join Pete Conrad on the surface.'],
  ['a12a.1334601', '12/surveyor-3.jpg', 'AS12-48-7133', 'Pete Conrad examines Surveyor 3\'s TV camera before removing it to bring home, with Intrepid on the horizon behind him.'],
  ['a12a_244_22_30_to_244_36_24', '12/recovery.jpg', '6903665', 'After splashdown, the Apollo 12 crew wave as they walk into the Mobile Quarantine Facility aboard the USS Hornet.'],
  ['a13_0000002ag', '13/launch.jpg', 'S70-34852', 'Apollo 13 lifts off from Pad 39A at 2:13 p.m. EST, April 11, 1970.'],
  ['a13_0555519', '13/damaged-service-module.jpg', 'as13-59-8500', 'The crew didn\'t see the damage until just before reentry: this photo, taken as the Service Module was jettisoned, shows the panel the oxygen tank explosion blew away.'],
  ['a14-0000025', '14/launch.jpg', 'S71-17620', 'Apollo 14 lifts off on January 31, 1971, seen from a camera on the mobile launcher.'],
  ['a14a_1354348', '14/golf-tv.jpg', 's71-20784', 'A frame from the live TV broadcast: Alan Shepard lines up a shot with a six-iron head attached to the contingency-sample handle, near the end of the second moonwalk.'],
  ['a15_0000013', '15/launch.jpg', 'S71-41356', 'Apollo 15 lifts off from Pad 39A on July 26, 1971.'],
  ['a15a1195255', '15/lrv.jpg', 'as15-85-11471', 'Dave Scott in the Lunar Roving Vehicle on the first moonwalk — the first time a rover was driven on the Moon.'],
  ['a15a1454747', '15/genesis-rock.jpg', 'S71-42955', 'The Genesis Rock (sample 15415) back on Earth in the Lunar Receiving Laboratory, August 1971.'],
  ['a15a1651703', '15/hadley-rille.jpg', 'as15-89-12100', 'A telephoto view across Hadley Rille, taken on the third moonwalk.'],
  ['a16_0000015', '16/launch.jpg', 'S72-35345', 'Apollo 16 lifts off from Pad 39A on April 16, 1972.'],
  ['a16a1232408', '16/big-muley.jpg', 's72-38465', 'Big Muley (sample 61016) in the Lunar Receiving Laboratory, May 1972, with geologist Bill Muehlberger, the rock\'s namesake (right).'],
  ['a17_0000027', '17/launch.jpg', 'S72-55070', 'Apollo 17 lifts off at 12:33 a.m. EST, December 7, 1972 — the only night launch of the program.'],
  ['a17_1125539csm', '17/challenger-on-surface.jpg', 'as17-134-20382', 'Challenger at Taurus-Littrow, with Harrison Schmitt, the flag and the rover — photographed two days after the landing.'],
  ['A17A1702454', '17/last-eva-ladder.jpg', 'S72-55299', 'From the live TV feed: Schmitt climbs Challenger\'s ladder at the end of the final moonwalk, minutes before Cernan\'s last words on the surface.'],
]

export const photosByClipId = Object.fromEntries(
  photos.map(([clipId, file, nasaId, caption]) => [
    clipId,
    {
      src: `photos/${file}`,
      caption,
      credit: `NASA (${nasaId.toUpperCase()})`,
      sourceUrl: `https://images.nasa.gov/details/${nasaId}`,
    },
  ]),
)
