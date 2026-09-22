// Real headshots for the crew of every digitized mission (Apollo 8, 10-17)
// plus the handful of recurring CAPCOMs/Mission Control voices, several of
// whom were themselves astronauts on other flights. Anyone not in this map
// falls back to a colored initials badge — expected for the ~250 other,
// rarer speaker labels found in the transcripts. Images live in
// public/speakers/<key>.jpg; keys are lowercased last names as normalized
// below.
//
// Sources: official NASA portrait photographs, verified via NASA/Wikimedia
// Commons (public domain, PD-USGov-NASA).

export const speakerPhotos = {
  // Crew
  borman: 'borman.jpg',
  lovell: 'lovell.jpg',
  anders: 'anders.jpg',
  stafford: 'stafford.jpg',
  young: 'young.jpg',
  cernan: 'cernan.jpg',
  armstrong: 'armstrong.jpg',
  collins: 'collins.jpg',
  aldrin: 'aldrin.jpg',
  conrad: 'conrad.jpg',
  gordon: 'gordon.jpg',
  bean: 'bean.jpg',
  swigert: 'swigert.jpg',
  haise: 'haise.jpg',
  shepard: 'shepard.jpg',
  roosa: 'roosa.jpg',
  mitchell: 'mitchell.jpg',
  scott: 'scott.jpg',
  worden: 'worden.jpg',
  irwin: 'irwin.jpg',
  mattingly: 'mattingly.jpg',
  duke: 'duke.jpg',
  evans: 'evans.jpg',
  schmitt: 'schmitt.jpg',
  mcdivitt: 'mcdivitt.jpg',
  schweickart: 'schweickart.jpg',

  // Frequent CAPCOMs / Mission Control voices
  allen: 'allen.jpg',
  fullerton: 'fullerton.jpg',
  mccandless: 'mccandless.jpg',
  carr: 'carr.jpg',
  henize: 'henize.jpg',
  overmyer: 'overmyer.jpg',
  hartsfield: 'hartsfield.jpg',
  lousma: 'lousma.jpg',
  peterson: 'peterson.jpg',
  gibson: 'gibson.jpg',
  kerwin: 'kerwin.jpg',
}

// Transcripts tag some lines with a channel/location suffix on the same
// person's name ("Duke (LM onboard)", "Mitchell-LM", "Cernan (in Snoopy)"),
// which would otherwise miss the plain-name key. Strip those down to the
// bare name so all of a person's lines resolve to one photo.
function normalizeSpeakerName(name) {
  return name
    .trim()
    .toLowerCase()
    .replace(/\(.*?\)/g, '')
    .split(/[/,]/)[0]
    .replace(/-.*$/, '')
    .trim()
}

export function speakerAvatar(name) {
  const key = normalizeSpeakerName(name)
  return speakerPhotos[key] ? `${import.meta.env.BASE_URL}speakers/${speakerPhotos[key]}` : null
}
