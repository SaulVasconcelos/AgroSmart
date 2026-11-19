#!/bin/sh
cd "$(dirname "$0")" || exit 1
if [ ! -f "data/raw/sensores.jsonl" ]; then python3 main.py demo || exit 1; fi
exec python3 main.py web
