"""Upload finished photos to Cloudflare R2, leaving out rejected frames.

Copies <media>/photos/<mission>/<frame>.jpg and .thumb.jpg to
r2:apollo-media/photos/..., only files that are new or changed, and deletes
from R2 any photo a reviewer has since rejected. Needs the "r2" rclone remote
(bash pipeline/setup_r2.sh).

    python pipeline/upload_photos.py --media /media/mark/T7/apollo-media
"""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--media', required=True)
    ap.add_argument('--dest', default='r2:apollo-media/photos')
    ap.add_argument('--reviews', default=str(HERE / 'photo_reviews.json'))
    args = ap.parse_args()
    rclone = shutil.which('rclone') or str(Path.home() / '.local/bin/rclone')
    reviews = json.loads(Path(args.reviews).read_text())
    rejected = sorted(f for f, r in reviews.items() if r.get('verdict') == 'reject')
    paths = [f'{f[2:4]}/{f}{ext}' for f in rejected for ext in ('.jpg', '.thumb.jpg')]

    with tempfile.TemporaryDirectory() as tmp:
        rules = Path(tmp) / 'filter.txt'   # first matching rule wins
        rules.write_text(''.join(f'- /{p}\n' for p in paths) + '+ /*/*.jpg\n- *\n')
        subprocess.run([rclone, 'copy', str(Path(args.media).expanduser() / 'photos'), args.dest,
                        '--filter-from', str(rules), '--transfers', '16', '--checkers', '16',
                        '--stats-one-line', '--stats', '30s'], check=True)
        gone = Path(tmp) / 'rejected.txt'
        gone.write_text(''.join(p + '\n' for p in paths))
        subprocess.run([rclone, 'delete', args.dest, '--files-from', str(gone)], check=True)
    # Tell the site which frames now have a cleaned photo on R2, and which to hide.
    index = HERE.parent / 'public' / 'photo-index'
    photos = Path(args.media).expanduser() / 'photos'
    for mdir in sorted(p for p in photos.iterdir() if p.is_dir()):
        cleaned = sorted(f.stem for f in mdir.glob('*.jpg') if not f.stem.endswith('.thumb') and f.stem not in set(rejected))
        rej = [f for f in rejected if f[2:4] == mdir.name]
        (index / f'{mdir.name}.cleaned.json').write_text(json.dumps({'cleaned': cleaned, 'rejected': rej}, separators=(',', ':')))
    print(f'uploaded; {len(rejected)} rejected frames kept off R2; site lists written to {index}')
    subprocess.run(['python3', str(HERE / 'review_page' / 'build_site.py')], check=True)


if __name__ == '__main__':
    main()
