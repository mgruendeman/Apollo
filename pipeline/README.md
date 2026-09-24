# Media pipeline: NASA audio and film scans

Scripts for bringing the site's audio and photos onto our own hosting,
straight from NASA's public-domain sources. They're meant to run on a
computer with a large drive; every step can be stopped and restarted.

| Step | Script | Output |
|---|---|---|
| What NASA has | `survey_nasa_audio.py` | `nasa_audio_inventory.json` (already committed) |
| Download tapes | `download_nasa_audio.py` | original MP3/FLAC files |
| Clean up audio | `process_audio.py` | `.original.m4a` + `.clean.m4a` per file |
| Ear check | `make_listening_page.py` | `listen.html` to compare versions |
| Photos | `process_photos.py` | cropped 2048 px JPEGs + thumbnails |

## What NASA has (archive.org, NASA JSC Audio Control Room)

| Mission | MP3 | FLAC (lossless) |
|---|---|---|
| Apollo 8 | 16.5 GB, 189 h | 108 GB |
| Apollo 9 | 5.1 GB, 57 h | 30 GB |
| Apollo 10 | 18.7 GB, 208 h | 138 GB |
| Apollo 11 | 10.1 GB, 175 h | 97 GB |
| Apollo 12 | 8.5 GB, 133 h | 32 GB |
| Apollo 13 | 53.1 GB, 1,094 h (many channels) | 216 GB |
| Apollo 14 | 13.7 GB, 160 h | 103 GB |
| Apollo 15 | 11.2 GB, 132 h | 84 GB |
| Apollo 16 | 15.0 GB, 170 h | 111 GB |
| Apollo 17 | 16.4 GB, 191 h | 114 GB |
| **All** | **about 170 GB** | **about 1 TB** |

Apollo 7's audio is listed as "coming soon". The MP3s are about 190 kbps,
plenty for 1960s radio audio; FLAC only matters if we want lossless masters.

## One-time setup

1. Install **git**, **ffmpeg** and **Python 3.10 or 3.11**
   (macOS: `brew install git ffmpeg python@3.11`; Windows: the python.org
   installer and `winget install ffmpeg`).
2. Clone the repo and make a Python environment:

   ```sh
   git clone https://github.com/mgruendeman/Apollo.git && cd Apollo
   python3.11 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
   # torch 2.0 first: CPU build, or CUDA 11.8 if you have an NVIDIA card
   pip install torch==2.0.1 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cpu
   #   (NVIDIA: ...--index-url https://download.pytorch.org/whl/cu118)
   pip install -r pipeline/requirements.txt
   ```

   DeepFilterNet downloads its model from GitHub the first time it runs.
3. Pick a folder on the big drive, e.g. `/Volumes/Apollo` or `D:\Apollo`
   (called `$MEDIA` below).

## 1. Ear check first (about 15 minutes)

Tune the noise reduction on samples before processing hundreds of hours:

```sh
python pipeline/download_nasa_audio.py --missions 8 11 13 --files 2 --head-mb 8 --dest $MEDIA/audio-sample
python pipeline/process_audio.py $MEDIA/audio-sample --out $MEDIA/samples --clip 200 45 --atten-db 12 24
python pipeline/make_listening_page.py $MEDIA/samples --engine DeepFilterNet
# open $MEDIA/samples/listen.html in a browser
```

`--atten-db` caps how much noise may be removed (in dB): lower sounds more
natural, higher is cleaner but can make voices watery. Try other values
(e.g. `--atten-db 6 12 18`) until one sounds right, then use it below.
`--engine ffmpeg` uses ffmpeg's simpler built-in denoiser instead.

## 2. Download everything

```sh
python pipeline/download_nasa_audio.py --missions 8 9 10 11 12 13 14 15 16 17 --dest $MEDIA/audio-orig
```

About 170 GB of MP3; add `--format flac` for lossless (about 1 TB). Re-run
the same command after any interruption and it carries on.

## 3. Process everything

```sh
python pipeline/process_audio.py $MEDIA/audio-orig --out $MEDIA/audio --atten-db 12
```

Output keeps each file's exact length (so transcript timing still lines
up): `<tape>.original.m4a` and `<tape>.clean.m4a`, 48 kbps mono AAC, about
10-15 GB in total for both versions of the air-to-ground tapes. On a CPU
DeepFilterNet takes a long while for all missions (days); an NVIDIA card
cuts that to hours. Already-finished files are skipped.

## 4. Photos

**Strategy.**

1. **NASA's release first.** When NASA's Image Library has its own
   version of a frame, the site uses it, with NASA's caption, unedited.
   These are public-domain NASA works. There are about 700 such frames,
   and `scripts/fetch_nasa_frames.py` finds them.
2. **Our cleanup for everything else.** The other ~18,000 frames exist
   only as the raw JSC/ASU film scans, so this script turns those into
   web photos. The raw scan of a frame NASA also released goes last in
   the gallery.
3. **Host both ourselves.** When the site moves to Cloudflare, copy
   NASA's releases into R2 alongside our cleaned scans (a few hundred MB),
   so the site doesn't depend on NASA's servers.
4. **People check the automatic results.** Reviewers mark each cleaned
   photo *Looks good*, or adjust it with dials that preview as they drag:
   brightness, contrast, shadows, highlights, warmth, tint and
   saturation (-8 to +8 steps each), straighten (up to 10 degrees either
   way), rotate (quarter turns), plus *Colour off* or *Bad crop* and a
   note for anything the dials can't fix. Save the marks as JSON, as in
   `photo_reviews.json` (the pilot's first round), and re-run with
   `--reviews pipeline/photo_reviews.json`:
   - the dials are applied automatically (`tone_curve`, `adjust_colour`,
     `straighten`). The review page previews them with the same formulas,
     so keep the two in step;
   - colour and crop marks are written to `needs-hand-fix.tsv` in the
     output folder for a fix by hand.

   The pilot review page (`review_page/`, built with `build.py`) covers
   the 40 sample frames. On the real site
   this becomes a reviewer mode backed by a Cloudflare D1 table, since
   18,000 frames is too many for the pilot's store.

**Running it at home.** Photos only need `pip install pillow numpy` (not
the audio packages). Try one mission's first 30 frames and check the crop
sheet:

```sh
python pipeline/process_photos.py --missions 11 --limit 30 --work $MEDIA/scans --out $MEDIA/photos --preview $MEDIA/check-11.jpg
```

Then everything, applying the review marks:

```sh
python pipeline/process_photos.py --missions 8 9 10 11 12 13 14 15 16 17 --work $MEDIA/scans --out $MEDIA/photos \
    --reviews pipeline/photo_reviews.json --workers 4
```

| | Frames | Download | Kept on disk |
|---|---|---|---|
| All scans ("med", ~16.8 MB each) | 17,679 (plus 418 NASA released) | about 300 GB | 300 GB of scans + 11 GB of photos |
| With `--discard-scans` | same | about 300 GB | about 11 GB |

- Frames NASA released its own version of are skipped (the site uses
  NASA's); `--include-nasa` processes them too.
- Stop it any time: the same command carries on, skipping finished photos
  (`--force` redoes them). Reviewed photos are always redone.
- `--workers` photos at a time, each using one CPU core and about 1 GB of
  memory. Roughly 3 s of CPU per photo: about 15 h on one core, 4 h on four.
  The download (300 GB) is usually the slower part.
- Keeping the scans (no `--discard-scans`) means later re-runs after
  reviews don't download again; with it, each re-run photo downloads its
  scan again (~17 MB).
- After a review round: `--reviews pipeline/photo_reviews.json --only-reviewed`.
- Output: `$MEDIA/photos/<mission>/<frame>.jpg` (2048 px, ~570 KB) and
  `<frame>.thumb.jpg` (400 px, ~26 KB).

Colour: each photo gets a white balance that takes out the cast the film
has picked up with age (judged from what should be grey or white), then a
small tone curve. Both were checked against NASA's own processed versions
of 37 frames: casts went from a median of 10 (worst 39) to 2.4 (worst
4.2), within the range NASA's own versions show. `--tint-strength 0` and
`--no-tone-curve` turn them off. About 3 s per frame.

## Still to build

- **Placing NASA's tapes on the mission clock.** NASA's files are whole
  tapes, not clips. The plan: run speech recognition over each tape and
  match it against the journal clips already recognised
  (`scripts/align_transcripts.py`'s cache) to find each tape's start time.
- **Upload** to Cloudflare R2 (`rclone sync $MEDIA/audio r2:apollo-audio`)
  and point the site at it.
