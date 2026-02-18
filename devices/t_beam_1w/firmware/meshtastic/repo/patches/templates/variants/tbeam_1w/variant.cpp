#include "variant.h"

// Some Meshtastic versions expect a variant init hook; others don't.
// Keep this file minimal and let compile-time defines drive behavior.

void variantInit() {
  // Optional: initialize I2C pins, power rails, etc.
}
