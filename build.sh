#!/bin/bash
set -euo pipefail

BORIS_BIN="${BORIS_BIN:-./bin/boris}"
DIST_DIR="${DIST_DIR:-dist}"

echo "🐘 Building drawmeanelephant.com static site using Boris..."
# Boris owns the generated tree; remove old pages so deleted content cannot linger.
if [ -d "$DIST_DIR" ]; then
  find "$DIST_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
fi

"$BORIS_BIN" --input content --theme themes/drawmeanelephant --html-dir "$DIST_DIR" \
  --layout-rule default 'glob:posts/*' themes/drawmeanelephant/layouts/post.html \
  --layout-rule default 'glob:breweries/*' themes/drawmeanelephant/layouts/brewery.html \
  --layout-rule default 'glob:other-places/*' themes/drawmeanelephant/layouts/brewery.html \
  --layout-rule default 'id:instagram' themes/drawmeanelephant/layouts/instagram-index.html \
  --layout-rule default 'glob:instagram/tags/*' themes/drawmeanelephant/layouts/instagram.html \
  --layout-rule default 'glob:instagram/*/*/*/*' themes/drawmeanelephant/layouts/instagram.html \
  -j 8
echo "🎉 Build complete! Output is located in the '$DIST_DIR' folder."
