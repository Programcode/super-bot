#!/usr/bin/env bash
# fetch_vendor.sh: download the vendor 3D models used by the photoreal renders and convert them
# to meshes. The models are not committed (size, and their licences are the vendors').
# All sources need no login.
#   Raspberry Pi 5 STEP (MIT, Raspberry Pi Ltd)          datasheets.raspberrypi.com
#   Camera Module 3 STEP (no licence stated)              datasheets.raspberrypi.com
#   Circuit Playground Express, BNO085, 1.3" TFT (MIT)    github.com/adafruit/Adafruit_CAD_Parts
#   LDROBOT LD19 STEP (no licence stated)                 github.com/ldrobotSensorTeam/Product_3D_model
# Not published by the vendor (the Fusion stand-ins stay): Pi Active Cooler, AI HAT+ 2.
# Usage: cad/v2/render/fetch_vendor.sh [dir]   (default /tmp/sbr/vendor; meshes go to <dir>/../vm)
set -euo pipefail
dir="${1:-/tmp/sbr/vendor}"
vm="$(dirname "$dir")/vm"
py="$HOME/tools/sb-ocp/bin/python"   # venv with cadquery-ocp==7.8.1.1.post1 and numpy
here="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$dir" "$vm"
ada=https://raw.githubusercontent.com/adafruit/Adafruit_CAD_Parts/main
get() { mkdir -p "$dir/$1"; [[ -s "$dir/$1/$2" ]] || curl -fsSL "$3" -o "$dir/$1/$2"; }
get pi5 pi5.zip https://datasheets.raspberrypi.com/rpi5/RaspberryPi5-step.zip
get cm3 cm3.zip https://datasheets.raspberrypi.com/camera/camera-module-3-step.zip
get ld19 ld19.zip https://github.com/ldrobotSensorTeam/Product_3D_model/releases/download/v1.0/LDROBOT_LiDAR_LD19_3D_STP_V1.0.zip
get cpx 3333-CircuitPlaygroundExpress.step "$ada/3333%20Circuit%20Playground%20Express/3333%20Circuit%20Playground%20Express.step"
get bno085 4754-BNO085-STEMMA-QT.step "$ada/4754%20BNO085%20STEMMA%20QT/4754%20BNO085%20STEMMA%20QT.step"
get tft13 4313-1.3in-TFT-IPS-Display.step "$ada/4313%201.3in%20TFT%20IPS%20Display/4313%201.3in-TFT-IPS-Display.step"
for z in pi5 cm3 ld19; do (cd "$dir/$z" && unzip -oq "$z.zip"); done
conv() { [[ -s "$vm/$1.bin" ]] || "$py" -I "$here/step2mesh.py" "$2" "$vm/$1" 0.03 8; }
conv pi5 "$(find "$dir/pi5" -name '*.step' | head -1)"
conv cm3 "$(ls "$dir"/cm3/*std*.stp | head -1)"
conv ld19 "$(find "$dir/ld19" -name '*ld19*.stp' | head -1)"
conv cpx "$dir/cpx/3333-CircuitPlaygroundExpress.step"
conv bno "$dir/bno085/4754-BNO085-STEMMA-QT.step"
conv tft "$dir/tft13/4313-1.3in-TFT-IPS-Display.step"
ls -la "$vm"
