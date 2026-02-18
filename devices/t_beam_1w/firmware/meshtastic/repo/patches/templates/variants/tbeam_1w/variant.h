#pragma once

// LilyGO T-Beam 1W (ESP32-S3) variant template
//
// IMPORTANT: Do not guess pins. Fill these in from docs/TBEAM_1W_PINMAP.md.

// -----------------
// LoRa: SX1262 + 1W front end
// -----------------
#define LORA_SCK    GPIO_NUM_NC
#define LORA_MISO   GPIO_NUM_NC
#define LORA_MOSI   GPIO_NUM_NC
#define LORA_CS     GPIO_NUM_NC

#define LORA_RESET  GPIO_NUM_NC
#define LORA_BUSY   GPIO_NUM_NC
#define LORA_DIO1   GPIO_NUM_NC

// High-power front-end control (names vary by schematic)
#define LORA_TXEN   GPIO_NUM_NC  // PA_EN / TX_EN
#define LORA_RXEN   GPIO_NUM_NC  // LNA_EN / RX_EN

// -----------------
// I2C: OLED + PMU
// -----------------
#define I2C_SDA     GPIO_NUM_NC
#define I2C_SCL     GPIO_NUM_NC

// -----------------
// Display
// -----------------
// Common on T-Beam family: SH1106 on I2C. Verify before enabling.
// #define USE_SH1106

// -----------------
// GNSS (L76K)
// -----------------
#define GPS_RX      GPIO_NUM_NC
#define GPS_TX      GPIO_NUM_NC
#define GPS_BAUD    9600

// -----------------
// Buttons / LEDs
// -----------------
#define BUTTON_USER GPIO_NUM_NC
#define LED_PIN     GPIO_NUM_NC

// -----------------
// Power Management
// -----------------
// Common on newer boards: AXP2101. Verify and enable if supported by your Meshtastic version.
// #define HAS_PMU_AXP2101 1
