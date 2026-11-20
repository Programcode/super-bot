#!/usr/bin/env bash
# fetch_assets.sh: download the render-only assets (not committed: size and licences).
# HDRIs and floor textures are CC0 from Poly Haven (polyhaven.com, no login).
# Usage: cad/v2/render/fetch_assets.sh [dest]   (default ~/ops/sb-render-assets)
set -euo pipefail
dest="${1:-$HOME/ops/sb-render-assets}"
mkdir -p "$dest"
ph=https://dl.polyhaven.org/file/ph-assets
get() { [[ -s "$dest/$2" ]] || curl -fsSL "$1" -o "$dest/$2"; }
get "$ph/HDRIs/hdr/2k/studio_small_09_2k.hdr" studio_small_09_2k.hdr
get "$ph/HDRIs/hdr/2k/lebombo_2k.hdr" lebombo_2k.hdr
for m in diff nor_gl rough; do
  get "$ph/Textures/jpg/2k/laminate_floor_02/laminate_floor_02_${m}_2k.jpg" "laminate_floor_02_${m}_2k.jpg"
done
ls -la "$dest"
