#!/bin/bash
set -e
echo "🐘 Building drawmeanelephant.com static site using Boris..."
./bin/boris --input content --theme themes/drawmeanelephant --html-dir dist \
  --layout-rule default 'glob:posts/*' themes/drawmeanelephant/layouts/post.html \
  --layout-rule default 'glob:breweries/*' themes/drawmeanelephant/layouts/brewery.html \
  --layout-rule default 'glob:instagram/*' themes/drawmeanelephant/layouts/brewery.html \
  -j 8
echo "🎉 Build complete! Output is located in the 'dist' folder."
