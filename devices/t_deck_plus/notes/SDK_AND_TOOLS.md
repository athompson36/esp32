# T-Deck Plus — SDKs & Tools

**Device:** LilyGO T-Deck Plus  
**Container:** platformio-lab (Launcher/Meshtastic) or future esp-idf-lab (LVGL/ESP-IDF)  
**Current projects:** LoRa mesh (2), maps/Launcher.

---

## Build (in container)

| Tool / SDK | Purpose |
|------------|--------|
| **Launcher** | LVGL, ESP-IDF, Rust, or MicroPython — see [bmorcelli/Launcher](https://github.com/bmorcelli/Launcher). |
| **Meshtastic** | PlatformIO, env e.g. `t-deck-tft`. |
| **Map tiles** | [JustDr00py/tdeck-maps](https://github.com/JustDr00py/tdeck-maps) — generator; run where Python/pip available. |

---

## Input calibration (Meshtastic)

- **Scroll ball speed:** Meshtastic firmware (T-Deck variant) throttles trackball direction events so only 1 in every N is sent (input calibration). Default `TRACKBALL_SCROLL_DIVISOR=2` (half speed). To change: in the Meshtastic repo set in the T-Deck variant `variant.h` or in `platformio.ini` for the t-deck env: `build_flags = -DTRACKBALL_SCROLL_DIVISOR=3` for slower scroll (1=full speed, 2=half, 3=one-third).

## Flash & serial (host)

| Tool | Purpose |
|------|---------|
| **esptool** | Flash Launcher or Meshtastic (T-Deck Plus). Download mode: hold trackball, power on. |
| **Serial** | Config, Meshtastic/Launcher CLI. |

---

## Docker dependencies (platformio-lab)

- PlatformIO, esptool, pyserial, picocom/screen.  
- For Launcher ESP-IDF native: consider esp-idf-lab with ESP-IDF + LVGL.

See [docker/TOOLS_AND_SDK.md](../../../docker/TOOLS_AND_SDK.md).
