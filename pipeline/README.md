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

```sh
python pipeline/process_photos.py --mission 11 --limit 30 --size med --work $MEDIA/scans --out $MEDIA/photos --preview $MEDIA/check-11.jpg
```

Check the preview sheet (red box = crop) before running whole missions
without `--limit`. The "med" scans are about 3,550 x 4,000 px, 14-18 MB
each (about 290 GB for all 18,000 frames); keep them as masters. The web
JPEGs come to about 9 GB.

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
