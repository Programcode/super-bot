#!/usr/bin/env bash
# run gen/cleanup.py until a round removes nothing (each process does one round)
B=${1:-main-board.kicad_pcb}
for i in 1 2 3 4 5 6; do
  out=$(~/tools/kicad-mcp-server/.venv/bin/python gen/cleanup.py "$B" 2>&1 | grep "^round")
  echo "$out"
  echo "$out" | grep -q "'via': 0, 'track': 0, 'silk': 0, 'ref': 0" && break
done
