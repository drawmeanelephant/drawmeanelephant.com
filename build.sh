#!/bin/bash
set -e
echo "🐘 Building drawmeanelephant.com static site using Boris..."
./bin/boris --input content --theme themes/drawmeanelephant --html-dir dist -j 8
echo "🎉 Build complete! Output is located in the 'dist' folder."
