#!/usr/bin/env bash
# After a review session: pull the marks from the site, redo the photos that
# were marked (adjusted, rotated, un-rejected), upload them, and rebuild the
# reviewer page. Then commit and push so the site picks up the new lists.
#
#   bash pipeline/apply_reviews.sh /media/mark/T7/apollo-media
set -euo pipefail
MEDIA="${1:?give the media folder, e.g. /media/mark/T7/apollo-media}"
cd "$(dirname "$0")/.."
python3 pipeline/reviews_sync.py pull
python3 pipeline/process_photos.py --reviews pipeline/photo_reviews.json --only-reviewed \
  --work "$MEDIA/scans" --out "$MEDIA/photos" --workers 8
python3 pipeline/upload_photos.py --media "$MEDIA"
echo "Done. Commit and push public/photo-index/*.cleaned.json, public/review/ and pipeline/photo_reviews.json."
