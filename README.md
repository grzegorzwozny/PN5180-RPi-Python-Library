# Library for PN5180 NFC Frontend

This libary a Python version of the libary published by @ATrappmann (https://github.com/ATrappmann/PN5180-Library). 

The library has been adapted to work under the control of the Linux (Rasbian) operating system. The software was tested on a Raspberry Pi 4 Compute Module.

This library currently only supports the ISO14443 standard.

## Hardware Configuration
Below is how to connect the PN5180 to the Raspberry Pi Compute Module. In this case, the hardware SPI0 interface was used. The SPI0 pins are GPIO 7, 8, 9, 10, 11.

| PN5180 | Raspberry Pi 4 Compute Module |
|--|--|
| Pin 1: NSS | Pin 36: GPIO8 |
| Pin 3: MOSI | Pin 44: GPIO10 |
| Pin 5: MISO | Pin 40: GPIO9 |
| Pin 7: SCK | Pin 38: GPIO11 |
| Pin 8: BUSY | Pin 29: GPIO16 |
| Pin 10: RESET_N | Pin 28: GPIO13 |
| Pin 39: IRQ | Pin 47: GPIO23 |

