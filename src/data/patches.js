// The missions' official emblems (crew patches): NASA artwork, cut out by
// scripts/make_patches.py, shown on the home page's mission cards.
const files = import.meta.glob('../assets/patches/*.webp', { eager: true, import: 'default' })

export function patchFor(missionId) {
  return files[`../assets/patches/apollo${missionId}.webp`] || null
}
