# firmware/esp32

ESP32-S3 firmware (PlatformIO). The reflex layer at ~1 kHz that always wins: 200 ms no-command stop, too-close braking, cliff, pickup/tilt motor cut, e-stop, stall/overcurrent, speed and accel limits, low-battery limp mode, and encoder speed control for the 4 mecanum motors (BTS7960 drivers). Talks to the Pi over USB serial / UART. No ESP32-S3s are owned yet; prototype on the ELEGOO UNO.
