"""Common project templates by controller/platform for project planning."""

# Controller IDs used in the UI (dropdown). Keep in sync with PROJECT_TEMPLATES keys.
CONTROLLER_IDS = [
    ("esp32", "ESP32"),
    ("raspberry_pi", "Raspberry Pi"),
    ("teensy", "Teensy"),
    ("arduino", "Arduino"),
    ("pine64", "Pine64 / Rock"),
    ("esp32_sbc", "ESP32 + SBC (hybrid)"),
    ("other", "Other"),
]

# Templates per controller: id, name, short description, optional prompt to seed the AI chat.
PROJECT_TEMPLATES = {
    "esp32": [
        {
            "id": "midi-controller",
            "name": "MIDI controller",
            "description": "USB/BLE MIDI controller with buttons, encoders, OLED; optional CV/gate for modular.",
            "prompt": "I want to build a MIDI controller with ESP32: USB and BLE MIDI, buttons, encoders, and small OLEDs for feedback. Optional CV/gate outputs for modular synth.",
        },
        {
            "id": "lora-mesh-node",
            "name": "LoRa mesh node",
            "description": "LoRa mesh node for messaging, sensors, or telemetry (e.g. T-Beam style).",
            "prompt": "I want to build a LoRa mesh node with ESP32 (e.g. T-Beam style): LoRa messaging, optional sensors, battery/solar, and maybe NFC.",
        },
        {
            "id": "environmental-sensor",
            "name": "Environmental sensor node",
            "description": "Temp/humidity/air quality node reporting over Wi-Fi or MQTT.",
            "prompt": "I want an ESP32 environmental sensor node: temp, humidity, air quality, reporting over Wi-Fi or MQTT to a central server. Low-power or solar option.",
        },
        {
            "id": "led-display-node",
            "name": "LED / display node",
            "description": "ESP32 driving LED matrix or OLED for visualizations, status, or art installations.",
            "prompt": "I want ESP32 nodes driving LED matrix or OLED displays: real-time visualizations, MQTT/WebSocket data, or art installation control (DMX/serial).",
        },
        {
            "id": "custom-firmware-device",
            "name": "Custom firmware device",
            "description": "Custom firmware on an existing board (e.g. Meshtastic-style, or bespoke app).",
            "prompt": "I want to run custom firmware on an ESP32 board (e.g. T-Beam/T-Deck): define features, UI, and radio/serial protocol. Suggest BOM and pinout.",
        },
        {
            "id": "art-installation",
            "name": "Art installation controller",
            "description": "Multi-node control for lighting, motors, sensors in interactive installations.",
            "prompt": "I want multi-node ESP32 controllers for an art installation: lighting (DMX/serial), motors, sensors, Wi-Fi sync between nodes.",
        },
    ],
    "raspberry_pi": [
        {
            "id": "digital-mixer",
            "name": "Digital mixer",
            "description": "Multi-input audio mixer with web UI, DSP, and hardware I/O.",
            "prompt": "I want a Raspberry Pi digital mixer: multi-input audio, DSP routing, web UI control surface, scenes and effects.",
        },
        {
            "id": "dashboard-server",
            "name": "Dashboard / data server",
            "description": "Pi as central server for Grafana/InfluxDB, MQTT, or sensor dashboards.",
            "prompt": "I want a Raspberry Pi as a central dashboard server: MQTT/HTTP ingestion, Grafana or similar, and optional local display.",
        },
        {
            "id": "access-control",
            "name": "Access control server",
            "description": "Badge/RFID auth, user management, logging, relay outputs.",
            "prompt": "I want a Raspberry Pi access control system: badge/RFID readers (could be ESP32 peripherals), user management, logging, relay outputs for locks.",
        },
        {
            "id": "media-player",
            "name": "Media player / jukebox",
            "description": "Local playback, custom UI, optional remote control.",
            "prompt": "I want a Raspberry Pi media player or jukebox: local file playback, web or touch UI, optional remote control.",
        },
        {
            "id": "effects-rack",
            "name": "Networked effects rack",
            "description": "Low-latency audio effects, web patching, distributed DSP.",
            "prompt": "I want a Raspberry Pi networked effects rack: low-latency audio processing, web UI for patching, multiple Pis for distributed DSP.",
        },
    ],
    "teensy": [
        {
            "id": "teensy-midi",
            "name": "MIDI controller / instrument",
            "description": "USB MIDI with low latency; buttons, encoders, optional audio.",
            "prompt": "I want a Teensy-based MIDI controller or instrument: USB MIDI, buttons, encoders, optional audio I/O and DSP.",
        },
        {
            "id": "teensy-audio",
            "name": "Audio DSP device",
            "description": "Real-time audio processing, effects, or synthesizer.",
            "prompt": "I want a Teensy audio device: real-time DSP, effects or synth, audio in/out, and control interface.",
        },
    ],
    "arduino": [
        {
            "id": "arduino-sensor",
            "name": "Sensor / data logger",
            "description": "Analog/digital sensors, serial or simple wireless reporting.",
            "prompt": "I want an Arduino project: sensors (analog/digital), data logging, serial or simple wireless output.",
        },
        {
            "id": "arduino-motor-control",
            "name": "Motor / servo control",
            "description": "Stepper or servo control, optional serial/UI.",
            "prompt": "I want Arduino motor or servo control: steppers/servos, optional serial or simple UI for sequencing.",
        },
    ],
    "pine64": [
        {
            "id": "pine-server",
            "name": "Server / dashboard",
            "description": "Pine/Rock as server or dashboard (similar to Pi use cases).",
            "prompt": "I want to use a Pine64 or Rock64 board as a server or dashboard: same kind of use as Raspberry Pi (data, media, access control).",
        },
    ],
    "esp32_sbc": [
        {
            "id": "hybrid-media",
            "name": "ESP32 + Pi media player",
            "description": "ESP32 for physical controls, Pi for playback and UI.",
            "prompt": "I want a hybrid media system: ESP32 for physical controls (knobs/buttons), Raspberry Pi for audio/video playback and UI. Serial or Wi-Fi link.",
        },
        {
            "id": "hybrid-access",
            "name": "ESP32 readers + Pi server",
            "description": "ESP32 RFID/NFC readers around site, Pi backend for auth and logging.",
            "prompt": "I want distributed access control: ESP32 RFID/NFC readers around the site, Raspberry Pi server for authentication, logging, and relay control.",
        },
    ],
    "other": [],
}


def list_controllers():
    """Return list of { id, name } for the controller dropdown."""
    return [{"id": cid, "name": name} for cid, name in CONTROLLER_IDS]


def get_templates(controller: str = None):
    """
    Return templates for the given controller. If controller is None or empty,
    returns all templates grouped by controller (for optional UI).
    """
    controller = (controller or "").strip().lower()
    if not controller:
        return {
            "controllers": list_controllers(),
            "templates_by_controller": {cid: PROJECT_TEMPLATES.get(cid, []) for cid, _ in CONTROLLER_IDS},
        }
    templates = PROJECT_TEMPLATES.get(controller, [])
    return {"controller": controller, "templates": templates}
