# Name:         PN5180 Python Library
# Description:  The PN5180 Protocols implementation.
#
# Copyright (c) 2021 by Grzegorz Wozny. All rights reserved.
#
# Based on 3rd Part Solution:
#       by Andreas Trappmann:   https://github.com/ATrappmann/PN5180-Library
#

from PN5180 import PN5180, regs

class ISO14443(PN5180):
    def __init__(self, bus, device, nns_pin, busy_pin, rst_pin, irq_pin):
        super().__init__(bus, device, nns_pin, busy_pin, rst_pin, irq_pin)

    def rx_bytes_received(self):
        pass

    # ------------------------------------
    #       Mifare Typa A Functions

    def mifare_activate_type_A(self, buffer, kind):
        '''buffer : must be 10 byte array
        buffer[0-1] is ATQA
        buffer[2] is sak
        buffer[3-6] is 4 byte UID
        buffer[7-9] is remaining 3 bytes of UID 7 Byte UID tags
        kind : 0 we send REQA, 1 we send WUPA
        
        return value: the uid length:
         - zero if no tag was recognized
         - single Size UID (4 byte)
         - double Size UID (7 byte)
         - triple Size UID (10 byte) - not yet supported'''

        cmd = [None] * 7
        uid_length = 0
        # Load standard TypeA protocol
        if (not PN5180.load_rf_config(self, 0x0, 0x80)): return 0
        # OFF Crypto
        if (not PN5180.write_register_with_and_mask(self, regs._SYSTEM_CONFIG, 0xFFFFFFBF)): return 0
        # Clear RX CRC
        if (not PN5180.write_register_with_and_mask(self, regs._CRC_RX_CONFIG, 0xFFFFFFFE)): return 0
        # Clear TX CRC
        if (not PN5180.write_register_with_and_mask(self, regs._CRC_TX_CONFIG, 0xFFFFFFFE)): return 0
        # Send REQA/WUPA, 7 bits in last byte
        cmd[0] = 0x26 if kind == 2 else 0x52
        if (not PN5180.send_data(self, cmd, 1, 0x07)): return 0
        # READ 2 bytes ATQA into buffer
        if (not PN5180.read_data(self, 2, buffer)): return 0
        # Send Anti collision 1, 8 bits in last byte
        cmd[0] = 0x93
        cmd[1] = 0x20
        if (not PN5180.send_data(self, cmd, 2, 0x00)): return 0
        # Read 5 bytes, we will store at offset 2 for later usage
        tmp = []
        if (not PN5180.read_data(self, 5, tmp)): return 0
        cmd[2] = tmp
        cmd = list(self.flatten(cmd))
        # Enable RX CRC calculation
        if (not PN5180.write_register_with_or_mask(self, regs._CRC_RX_CONFIG, 0x01)): return 0
        # Enable TX CRC calculation
        if (not PN5180.write_register_with_or_mask(self, regs._CRC_TX_CONFIG, 0x01)): return 0
        # Send Select anti collision 1, the remaining bytes are already in offset 2 onwards
        cmd[0] = 0x93
        cmd[1] = 0x70
        # print("CMD: --> ", cmd)
        if (not PN5180.send_data(self, cmd, 7, 0x00)): return 0
        # Read 1 byte SAK into buffer[2]
        tmp = []
        if (not PN5180.read_data(self, 1, tmp)): return 0
        buffer[2] = tmp
        buffer = list(self.flatten(buffer))
        # Check if the tag is 4 Byte UID or 7 byte UID and requires anti collision 2
        # If Bit 3 is 0 it is 4 Byte UID
        if ((buffer[2] & 0x04) == 0):
            # Take first 4 bytes of anti collision as UID store at offset 3 onwards. Job Done.
            for i in range(4):
                buffer[i + 3] = cmd[i + 2]
                print ("  Card Serial Number: 0x{:02x}".format(buffer[i + 3]))
            uid_length = 4
        else:
            # Take first 3 bytes of UID, Ignore first byte 88(CT)
            if (cmd[2] != 0x88):
                return 0
            for i in range(3):
                buffer[i + 3] = cmd[i + 3]
                print ("  Card Serial Number: 0x{:02x}".format(buffer[i + 3]))
            # Clear RX CRC
            if (not PN5180.write_register_with_and_mask(self, regs._CRC_RX_CONFIG, 0xFFFFFFFE)): return 0
            # Clear TX CRC
            if (not PN5180.write_register_with_and_mask(self, regs._CRC_TX_CONFIG, 0xFFFFFFFE)): return 0
            # Do anti collision 2
            cmd[0] = 0x95
            cmd[1] = 0x20
            if (not PN5180.send_data(self, cmd, 2, 0x00)): return 0
            # Read 5 bytes. We will sotre at offset 2 for later use
            tmp = []
            if (not PN5180.read_data(self, 5, tmp)): return 0
            cmd[2] = tmp
            cmd = list(self.flatten(cmd))
            #   first 4 bytes belongs to last 4 UID bytes, we keep it
            for i in range(4):
                buffer[i + 6] = cmd[i + 2]
                print ("  Card Serial Number: 0x{:02x}".format(buffer[i + 6]))
            # Enable RX CRC calculation
            if (not PN5180.write_register_with_or_mask(self, regs._CRC_RX_CONFIG, 0x01)): return 0
            # Enable TX CRC calculation
            if (not PN5180.write_register_with_or_mask(self, regs._CRC_TX_CONFIG, 0x01)): return 0
            # Send Select anti collision 2
            cmd[0] = 0x95
            cmd[1] = 0x70
            if (not PN5180.send_data(self, cmd, 7, 0x00)): return 0
            # Read 1 byte SAK into buffer[2]
            tmp = []
            if (not PN5180.read_data(self, 1, tmp)): return 0
            buffer[2] = tmp
            buffer = list(self.flatten(buffer))
            uid_length = 7
        
        return uid_length

    def mifare_block_read():
        pass

    def mifare_block_write_16():
        pass

    def mifare_halt():
        cmd = [None] * 1
        # Mifare Halt
        cmd[0] = 0x50
        cmd[1] = 0x00
        PN5180.send_data(self, cmd, 2, 0x00)
        return True

    # ------------------------------------

    # ------------------------------------
    #       Helper Functions

    def setup_rf(self):
        if (PN5180.load_rf_config(self, 0x00, 0x80)):  # ISO14443 Parameters
            print("Set Protocol ISO14443 - Done.")
        else:
            return False

        if (PN5180.set_rf_on(self)):
            print("RF Field is turned on.")
        else:
            return False

        return True

    def read_card_serial(self, buffer):
        response = []
        uid_length = 0
        # Always return 10 bytes
        # Offset 0..1 id ATQA
        # Offset 2 is SAK.
        # UID 4 bytes : offset 3 to 6 is UID, offset 7 to 9 to Zero
        # UID 7 bytes : offset 3 to 9 is UID
        
        for i in range(10): response.append(0)
        
        uid_length = self.mifare_activate_type_A(response, 1)
        # print("uid_length: -> ", uid_length)
        # print("response: -> ", response)
        
        if ((response[0] == 0xFF) and (response[1] == 0xFF)): return 0
        # check for valid uid
        if ((response[3] == 0x00) and (response[4] == 0x00) and (response[5] == 0x00) and (response[6] == 0x00)):
            return 0
        if ((response[3] == 0xFF) and (response[4] == 0xFF) and (response[5] == 0xFF) and (response[6] == 0xFF)):
            return 0
        
        for i in range(7):
            buffer[i] = response[i + 3]
        self.mifare_halt()
        
        return uid_length

    def is_card_present(self):
        buffer = []
        serial = self.read_card_serial(buffer)
        #print("serial: -> ", serial)
        return serial >= 4
    
    def flatten(self, list):
        '''Helper function for flatten an irregulat list of lists.'''
        for item in list:
            try:
                yield from self.flatten(item)
            except TypeError:
                yield item
    # ------------------------------------


class ISO15693(PN5180):
    def __init__(self):
        pass

    def run(self):
        print("Hello ISO15693")
