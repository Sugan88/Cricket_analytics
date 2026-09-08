#!/usr/bin/env bash
set -euo pipefail

# Downloads Australian men's international matches from Cricsheet.
# Data licensed under ODbL - see https://cricsheet.org/

RAW_DIR="data/raw"
URL="https://cricsheet.org/downloads/australia_male_json.zip"

mkdir -p "$RAW_DIR"
cd "$RAW_DIR"

echo "Downloading Australia men's matches from Cricsheet..."
curl -L -o australia_male_json.zip "$URL"

echo "Extracting..."
unzip -oq australia_male_json.zip -d australia_male

echo "Done: $(ls australia_male/*.json | wc -l) match files"
echo "Next: python data/processors/cricsheet_loader.py"
