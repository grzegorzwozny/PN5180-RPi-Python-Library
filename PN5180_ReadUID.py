# Name:         PN5180 Python Library
# Description:  Example usage of the PN5180 library for the PN5180-NFC Module
#               from NXP Semiconductors.
#
# Copyright (c) 2021 by Grzegorz Wozny. All rights reserved.
#
# Based on 3rd Part Libraries:
#       by Andreas Trappmann:   https://github.com/ATrappmann/PN5180-Library
#       by Dirk Carstensen:     https://github.com/tueddy/PN5180-Library/tree/ISO14443
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#

import PN5180
from Protocol import ISO14443, ISO15693
import time
import sys

# PN5180 Pins Definition
PN5180_SPI_BUS = 0
PN5180_SPI_DEV = 0
PN5180_NNS = 8
PN5180_BUSY = 16
PN5180_RST = 13
PN5180_IRQ = 23

nfc14443 = ISO14443(PN5180_SPI_BUS, PN5180_SPI_DEV, PN5180_NNS, PN5180_BUSY, PN5180_RST, PN5180_IRQ)
#nfc14443 = ISO14443()
#nfc15693 = ISO15693(PN5180_NNS, PN5180_BUSY, PN5180_RST)

# PN5180 Setup
print("*** PN5180 ***\n")
nfc14443.begin() # TODO: Check is this function is call

print("\nPN5180 Hard-Reset...")
nfc14443.reset() # TODO: Check is this function is call

print("\n\nReading product version...")
product_version = []
nfc14443.read_eeprom(PN5180._PRODUCT_VERSION, product_version, 2)
product_version = sum(product_version, [])[::-1]
print("Product version = {}.{}".format(product_version[0], product_version[1]))
#print("Product version = {}".format(product_version))

if ((0xff == product_version[1]) or 0xff == product_version[0]):
    print("Initialization failed!?")
    print("Reset the system, please")
    sys.exit()  # Halt execute

print("\n\nReading firmware version...")
firmware_version = []
nfc14443.read_eeprom(PN5180._FIRMWARE_VERSION, firmware_version, 2)
firmware_version = sum(firmware_version, [])[::-1]
print("Firmware version = {}.{}".format(firmware_version[0], firmware_version[1]))

print("\n\nReading EEPROM version...")
eeprom_version = []
nfc14443.read_eeprom(PN5180._EEPROM_VERSION, eeprom_version, 2)
eeprom_version = sum(eeprom_version, [])[::-1]
print("EEPROM version = {}.{}".format(eeprom_version[0], eeprom_version[1]))

print("\n\nEnable RF field...")
nfc14443.setup_rf()

loop_cnt = 0

while True:
    print("-----")
    loop_cnt += 1
    uid = []
    # Check for ISO14443 card
    nfc14443.reset() # TODO: Check is this function is call
    nfc14443.setup_rf()
    if (nfc14443.is_card_present()):
        
        uid_length = nfc14443.read_card_serial(uid)
        if (uid_length > 0):
            print("ISO14443 card found, UID=")
            for i in range(uid_length):
                print(" 0" if uid[i] < 0x10 else " ")
                print(uid[i]) # <-------------------------- TODO:Set print as HEX
    print("-----")
    time.sleep(1)

    # 
