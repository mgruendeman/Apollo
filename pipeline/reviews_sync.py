"""Move photo review marks between the site's database and photo_reviews.json.

    python pipeline/reviews_sync.py setup   # once: the site address and review password
    python pipeline/reviews_sync.py pull    # site -> pipeline/photo_reviews.json
    python pipeline/reviews_sync.py push    # photo_reviews.json -> site (only marks the site lacks)

The password is kept in ~/.config/apollo/review.json, readable only by you.
"""
import getpass
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CONF = Path.home() / '.config' / 'apollo' / 'review.json'
MARKS = Path(__file__).parent / 'photo_reviews.json'
KEYS = ('brightness', 'contrast', 'shadows', 'highlights', 'warmth', 'tint', 'saturation', 'straighten', 'rotate')


def call(conf, method, path, body=None):
    req = urllib.request.Request(conf['site'].rstrip('/') + '/api/review' + path, method=method,
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={'Authorization': f"Bearer {conf['password']}", 'Content-Type': 'application/json',
                                          'User-Agent': 'apollo-pipeline'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def compact(d):
    """The pipeline's form of a mark: only what's set."""
    r = {k: d[k] for k in KEYS if d.get(k)}
    for k in ('colour', 'crop'):
        if d.get(k):
            r[k] = True
    if d.get('note'):
        r['note'] = d['note']
    r['verdict'] = d.get('verdict')
    return r


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'setup':
        site = input('Site address [https://apollo.apollo-audio-files.workers.dev]: ').strip() or 'https://apollo.apollo-audio-files.workers.dev'
        conf = {'site': site, 'password': getpass.getpass('Review password (hidden): ')}
        call(conf, 'GET', '/me')
        CONF.parent.mkdir(parents=True, exist_ok=True)
        CONF.write_text(json.dumps(conf))
        CONF.chmod(0o600)
        print('Saved; the site accepted the password.')
        return
    conf = json.loads(CONF.read_text())
    if cmd == 'pull':
        remote = call(conf, 'GET', '/marks')['reviews']
        marks = {d['id']: compact(d['data']) for d in remote}
        MARKS.write_text(json.dumps(marks, indent=1, sort_keys=True))
        print(f'{len(marks)} marks saved to {MARKS.name}')
    elif cmd == 'push':
        have = {d['id'] for d in call(conf, 'GET', '/marks')['reviews']}
        marks = json.loads(MARKS.read_text())
        sent = 0
        for fid, m in marks.items():
            if fid in have:
                continue
            call(conf, 'PUT', f'/marks/{urllib.parse.quote(fid)}', {**m, 'by': 'pipeline'})
            sent += 1
        print(f'{sent} marks sent ({len(have)} were already on the site)')
    else:
        print(__doc__)


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as e:
        sys.exit(f'The site said {e.code}: {e.read().decode()[:200]}')
