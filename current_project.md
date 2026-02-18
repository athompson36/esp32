# Current Cyber-Lab Projects (ESP32 & SBC)
*Compiled for Andrew (athompson36) — projects either started, prototyped, or conceptualized involving ESP32 microcontrollers or single board computers (SBCs like Raspberry Pi).*

---

## 1. **Maschine MK2 ESP32 Mod**
**Platform:** ESP32 / Teensy hybrid  
**Status:** Concept / design phase  
**Description:**  
A custom mod for the Native Instruments Maschine MK2 where an ESP32/Teensy controller replaces or augments the stock MCU for expanded MIDI/OSC control, OLED displays, and programmable mappings.  
**Key Features:**  
- ESP32 handles Wi-Fi/MIDI over network  
- OLED scribble strips for visual feedback  
- Enhanced encoder/button handling  
- MIDI routing between hardware and DAW

**Notes:**  
Leverages ESP32’s networking and processing to modernize an older controller platform.

---

## 2. **LoRa Mesh Nodes (T-Beam / ESP32)**
**Platform:** ESP32 (TTGO T-Beam)  
**Status:** Field-tested / ongoing  
**Description:**  
LoRa mesh network using T-Beam ESP32 boards with NFC/SDR expansions. Designed for decentralized low-power messaging and sensor networks.  
**Key Features:**  
- LoRa communication across nodes (1W units)  
- NFC tag interactions  
- Optional SDR/expansion modules  
- Roof-mounted antennas and mesh routing

**Notes:**  
Applicable to rural/remote networking experiments and sensor aggregation.

---

## 3. **Raspberry Pi-Based Digital Mixer**
**Platform:** Raspberry Pi SBC  
**Status:** Planning/early build  
**Description:**  
A multi-input digital audio mixer running on a Raspberry Pi, with custom hardware I/O, web-based UI, and DSP handling.  
**Key Features:**  
- Pi 4/Compute for DSP audio routing  
- USB/ADC audio interfaces  
- Web UI control surface
- Scenes, effects, and automation

**Notes:**  
Blends software mixing with hardware controls; scalable to FOH or studio use.

---

## 4. **Custom ESP32 MIDI Controller**
**Platform:** ESP32  
**Status:** Concept  
**Description:**  
Standalone MIDI controller based on ESP32 with OLEDs, buttons, encoders, and CV outputs for modular synth integration.  
**Key Features:**  
- BLE & USB MIDI support
- Mini OLED feedback per control  
- Expandable I/O modules
- CV/Gate outputs via DAC/PWM

**Notes:**  
Designed for modular setups and DAW control.

---

## 5. **ESP32 Environmental Sensor Array**
**Platform:** ESP32  
**Status:** Concept  
**Description:**  
Multiple ESP32 nodes with environmental sensors (temp/humidity/air quality/light) reporting over Wi-Fi or mesh to a central SBC (Pi) for logging and dashboard display.  
**Key Features:**  
- MQTT/HTTP data delivery
- Pi dashboard (Grafana/InfluxDB)
- Solar/battery low-power modes

**Notes:**  
Useful for maker spaces, greenhouses, or workshop environment monitoring.

---

## 6. **ESP32-SBC Hybrid Media Player**
**Platform:** ESP32 + Raspberry Pi  
**Status:** Concept  
**Description:**  
An integrated media playback system where ESP32 handles physical controls (knobs/buttons) and Pi handles audio/video output. Communicates over serial/Wi-Fi.  
**Key Features:**  
- Custom UI via Pi
- Local file playback
- Remote control via ESP32 panel

**Notes:**  
Ideal for DIY portable jukebox or installation art.

---

## 7. **Pi SBC Security/Access Controller**
**Platform:** Raspberry Pi + ESP32 peripherals  
**Status:** Concept  
**Description:**  
Secure access control using Pi backend and ESP32 front-end devices (RFID/NFC readers) around a facility.  
**Key Features:**  
- Badge authentication via ESP32  
- Pi server with logging and user management  
- Relay outputs for door locks

**Notes:**  
Leverages ESP32 low cost for distributed hardware.

---

## 8. **ESP32-Driven Art Installation Controllers**
**Platform:** ESP32  
**Status:** Experimental  
**Description:**  
Multi-node ESP32 controllers for lighting, motors, sensors in interactive art installations (e.g., liquid light rigs, kinetic pieces).  
**Key Features:**  
- Real-time control loops  
- DMX/serial out to lighting rigs  
- Wi-Fi sync between nodes

**Notes:**  
Bridges digital control with analog/mechanical art.

---

## 9. **Raspberry Pi Networked Effects Rack**
**Platform:** Raspberry Pi SBC  
**Status:** Concept  
**Description:**  
Networked audio effects platform running on Pis, each dedicated to a specific effect, controlled via LAN.  
**Key Features:**  
- Low-latency audio processing  
- Web UI patching
- Distributed DSP

**Notes:**  
Scalable multi-box effects for live/studio.

---

## 10. **ESP32 Visualizer Display Nodes**
**Platform:** ESP32 + LED Matrix/OLED  
**Status:** Concept  
**Description:**  
ESP32 nodes driving displays (LED matrix/OLED) showing real-time audio/midi visualizations or environment metrics. Sync via Wi-Fi to master SBC or host.

**Key Features:**  
- WS2812/APA102 LED control  
- MQTT/Websocket feeds
- Audio reactive patterns

---

## 🧠 Notes & Next Steps
- Projects are ordered by **immediacy of build or past discussion relevance**.  
- For each project you may want to track: hardware BOM, schematic, firmware plan, user interface mockups, and target milestones.  
- If you want this as a **downloadable file**, I can generate a `.md` you can directly download.

---

## 🔧 Lab context (SDKs, tools, Docker)
- **SDKs & tools (all devices):** [docker/TOOLS_AND_SDK.md](docker/TOOLS_AND_SDK.md)  
- **Docker dependencies:** [docker/DEPENDENCIES.md](docker/DEPENDENCIES.md)  
- **Per-device SDK/tools:** `devices/<device>/notes/SDK_AND_TOOLS.md`  
- **Build:** `docker build -t platformio-lab -f docker/Dockerfile .` → build in container; flash from host (macOS).