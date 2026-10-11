#!/usr/bin/env sh
# index.html is written as a page fragment (the form Claude artifacts publish).
# This wraps it in a full document so it can be opened straight from disk.
set -e
cd "$(dirname "$0")"
{
  printf '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n</head><body>\n'
  cat index.html
  printf '\n</body></html>\n'
} > standalone.html
echo "Wrote standalone.html"
