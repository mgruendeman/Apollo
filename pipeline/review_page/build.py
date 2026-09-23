"""Build the photo review page (the pilot for the site's reviewer mode).

Joins template.html, script.js and frames.json into one page. Each frame in
frames.json has its image paths (`ours`, `raw`, `thumb`, optional `nasa` and
`before`), caption, and `rendered`: the dial settings the `ours` image was
made with, so the page's live preview can start from them.

    python pipeline/review_page/build.py out.html

The page stores marks in its host's shared store (on claude.ai, the
artifact's database), one record per frame; export them to the JSON that
`process_photos.py --reviews` reads. The live preview's formulas mirror
tone_curve / adjust_colour / straighten in process_photos.py.
"""
import json
import sys
from pathlib import Path

here = Path(__file__).parent
frames = json.loads((here / 'frames.json').read_text())
script = (here / 'script.js').read_text().replace('__FRAMES__', json.dumps(frames))
page = (here / 'template.html').read_text().replace('__SCRIPT__', script)
Path(sys.argv[1] if len(sys.argv) > 1 else 'photo-review.html').write_text(page)
