# platformio-lab: ESP32, Arduino, Teensy, Raspberry Pi, Pine64
# Build in container; flash from host.
# FROM ubuntu:22.04
ARG BASE_IMAGE=ubuntu:22.04
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    git \
    curl \
    wget \
    unzip \
    python3 \
    python3-pip \
    python3-venv \
    libusb-1.0-0 \
    udev \
    picocom \
    screen \
    gcc-arm-linux-gnueabihf \
    g++-arm-linux-gnueabihf \
    gcc-aarch64-linux-gnu \
    g++-aarch64-linux-gnu \
    && rm -rf /var/lib/apt/lists/*

# Pinned for reproducible builds. Update periodically; document in docker/DEPENDENCIES.md.
ARG PLATFORMIO_VERSION=6.1.19
ARG ESPTOOL_VERSION=4.11.0
ARG PYSERIAL_VERSION=3.5

# PlatformIO, ESP32/Arduino/Teensy/nRF52 toolchains (PIO installs per-platform on first build)
RUN pip3 install --no-cache-dir "platformio==${PLATFORMIO_VERSION}"

# ESP32: flash, merge_bin, image_info (T-Beam webflasher, CI, scripts).
# Pin by Git tag: PyPI sdists have broken metadata (project name "unknown") so install from GitHub.
RUN pip3 install --no-cache-dir "git+https://github.com/espressif/esptool.git@v${ESPTOOL_VERSION}"

# Serial scripting (config automation, repeater/room-server CLI)
RUN pip3 install --no-cache-dir "pyserial==${PYSERIAL_VERSION}"

# Optional: Arduino CLI for non-PIO Arduino workflows
RUN pip3 install --no-cache-dir arduino-cli || true

# LittleFS image tool (Meshtastic and other ESP32 firmware that build a data partition)
# Asset names: x86_64-linux-gnu-mklittlefs-*.tar.gz, aarch64-linux-gnu-mklittlefs-*.tar.gz
ARG MKLITTLEFS_VERSION=4.1.0
ARG MKLITTLEFS_COMMIT=42acb97
RUN set -e; \
  ARCH=$(dpkg --print-architecture); \
  case "$ARCH" in amd64) MKL_ARCH=x86_64-linux-gnu;; arm64) MKL_ARCH=aarch64-linux-gnu;; *) MKL_ARCH=x86_64-linux-gnu;; esac; \
  curl -sL "https://github.com/earlephilhower/mklittlefs/releases/download/${MKLITTLEFS_VERSION}/${MKL_ARCH}-mklittlefs-${MKLITTLEFS_COMMIT}.tar.gz" -o /tmp/mklittlefs.tar.gz; \
  tar -xzf /tmp/mklittlefs.tar.gz -C /tmp; \
  ( MKL_BIN=$(find /tmp -maxdepth 2 -name mklittlefs -type f | head -1); [ -n "$MKL_BIN" ] && install -m 0755 "$MKL_BIN" /usr/local/bin/ ); \
  rm -rf /tmp/mklittlefs*

WORKDIR /workspace

# Default: run shell so "docker run -it ..." works
CMD ["/bin/bash"]
