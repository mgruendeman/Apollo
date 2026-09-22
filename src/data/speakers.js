// Real NASA portrait photos for frequently-appearing speakers (crew plus
// the handful of recurring CAPCOMs/Mission Control voices — many of whom
// were themselves astronauts on other flights). Anyone not in this map
// falls back to a colored initials badge. Images live in
// public/speakers/<key>.jpg; keys are lowercased last names as they
// appear in the transcripts (e.g. "Conrad", "Duke").
//
// Populated by scripts/fetch_speaker_photos.py from verified Wikimedia
// Commons URLs — see that script for the source of each photo.

export const speakerPhotos = {}

export function speakerAvatar(name) {
  const key = name.trim().toLowerCase()
  return speakerPhotos[key] ? `${import.meta.env.BASE_URL}speakers/${speakerPhotos[key]}` : null
}
