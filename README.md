# Library for PN5180 NFC Frontend

This library is a Python adaptation of the original library by @ATrappmann ([available at ATrappmann's PN5180 Library](https://github.com/ATrappmann/PN5180-Library)).

The library has been modified to operate on the Linux (Raspberry OS) operating system and has been tested on the RPi CM4.

Currently, this library supports only the ISO14443 standard.

## Hardware Configuration
Below are the connection instructions for interfacing the PN5180 with the Raspberry Pi Compute Module using the hardware SPI0 interface. The SPI0 pins used are GPIO 7, 8, 9, 10, and 11.

| PN5180 | Raspberry Pi 4 Compute Module |
|--|--|
| Pin 1: NSS | Pin 36: GPIO8 |
| Pin 3: MOSI | Pin 44: GPIO10 |
| Pin 5: MISO | Pin 40: GPIO9 |
| Pin 7: SCK | Pin 38: GPIO11 |
| Pin 8: BUSY | Pin 29: GPIO16 |
| Pin 10: RESET_N | Pin 28: GPIO13 |
| Pin 39: IRQ | Pin 47: GPIO23 |

