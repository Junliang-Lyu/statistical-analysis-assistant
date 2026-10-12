#!/usr/bin/env bash
set -eu
origin="${1:-https://stats.jun-liang-lyu.com}"
expected="${2:-}"
body=$(curl -fsS --max-time 15 "$origin/api/health")
[ "$body" = '{"status":"ok"}' ] || { echo 'FAIL health'; exit 1; }
curl -fsS --max-time 15 "$origin/" >/dev/null
curl -fsS --max-time 15 "$origin/examples/trial.json" >/dev/null
if [ -n "$expected" ]; then
    actual=$(curl -fsS --max-time 15 "$origin/release.txt")
    [ "$actual" = "$expected" ] || { echo 'FAIL release version'; exit 1; }
fi
code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 -X POST -H 'Origin: https://invalid.example' -H 'Content-Type: application/json' -d '{}' "$origin/api")
[ "$code" = 403 ] || { echo 'FAIL origin guard'; exit 1; }
echo 'PASS stats health, page, fixture, version and origin guard; no paid model calls'
