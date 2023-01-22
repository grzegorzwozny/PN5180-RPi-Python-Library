# Name:         PN5180 Python Library
# Description:  The PN5180 core class.
#
# Copyright (c) 2021 by Grzegorz Wozny. All rights reserved.
#
# Based on 3rd Part Solution:
#       by Andreas Trappmann:   https://github.com/ATrappmann/PN5180-Library
#

import spidev
import RPi.GPIO as GPIO
import time
from enum import Enum

# PN5180 Registers
class regs:
    _SYSTEM_CONFIG  = 0x00
    # _IRQ_ENABLE         = 0x01
    _IRQ_STATUS = 0x02
    _IRQ_CLEAR = 0x03
    # _TRANSCEIVE_CONTROL = 0x04
    # _TIMER1_RELOAD      = 0x0c
    # _TIMER1_CONFIG      = 0x0f
    # _RX_WAIT_CONFIG     = 0x11
    _CRC_RX_CONFIG      = 0x12
    # _RX_STATUS          = 0x13
    # _TX_WAIT_CONFIG     = 0x17
    # _TX_CONFIG          = 0x18
    _CRC_TX_CONFIG      = 0x19
    _RF_STATUS          = 0x1d
    # _SYSTEM_STATUS      = 0x24
    # _TEMP_CONTRO        = 0x25
    # _AGC_REF_CONFIG     = 0x26

# PN5180 1-Byte Direct Commands
# see 11.4.3.3 Host Interface Command List
_PN5180_WRITE_REGISTER = 0x00  # Write one 32bit register value
# Sets one 32bit register value using a 32bit OR mask
_PN5180_WRITE_REGISTER_OR_MASK = 0x01
# Write one 32bit register value using a 32 bit AND mask
_PN5180_WRITE_REGISTER_AND_MASK = 0x02
_PN5180_READ_REGISTER = 0x04  # Reads one 32bit register value
# Processes an array of EEPROM addresses in random order and writes the value to these addresses
_PN5180_WRITE_EEPROM = 0x06
# Processes an array of EEPROM addresses from a start address and reads the values from these addresses
_PN5180_READ_EEPROM = 0x07
# This instruction is used to write data into the transmission buffer, the START_SEND bit is auto-set.
_PN5180_SEND_DATA = 0x09
# This instruction is used to read data from reception buffer, after successful reception
_PN5180_READ_DATA = 0x0A
# This instruction is used to switch the mode. It is only possible to switch from NormalMode to standby, LPCD or Autocoll
_PN5180_SWITCH_MODE = 0x0B
# This instruction is used to update the RF configuration from EEPROM into the configuration registers
_PN5180_LOAD_RF_CONFIG = 0x11
_PN5180_RF_ON = 0x16  # This instruction switch on the RF Field
_PN5180_RF_OFF = 0x17  # This instruction switch off the RF Field


# PN5180 EEPROM Addresses
_DIE_IDENTIFIER = 0x00
_PRODUCT_VERSION = 0x10
_FIRMWARE_VERSION = 0x12
_EEPROM_VERSION = 0x14
_IRQ_PIN_CONFIG = 0x1A

# PN5180 Transceiver States
class PN5180_Transceive_Stat(Enum):
  PN5180_TS_Idle            = 0
  PN5180_TS_WaitTransmit    = 1
  PN5180_TS_Transmitting    = 2
  PN5180_TS_WaitReceive     = 3
  PN5180_TS_WaitForData     = 4
  PN5180_TS_Receiving       = 5
  PN5180_TS_LoopBack        = 6
  PN5180_TS_RESERVED        = 7

# PN5180 IRQ_STATUS
# _RX_IRQ_STAT         	= 1<<0  # End of RF rececption IRQ
# _TX_IRQ_STAT         	= 1<<1  # End of RF transmission IRQ
_IDLE_IRQ_STAT = 1 << 2  # IDLE IRQ
# _RFOFF_DET_IRQ_STAT  	= 1<<6  # RF Field OFF detection IRQ
# _RFON_DET_IRQ_STAT   	= 1<<7  # RF Field ON detection IRQ
# _TX_RFOFF_IRQ_STAT   	= 1<<8  # RF Field OFF in PCD IRQ
_TX_RFON_IRQ_STAT = 1 << 9  # RF Field ON in PCD IRQ
# _RX_SOF_DET_IRQ_STAT 	= 1<<14 # RF SOF Detection IRQ
# _GENERAL_ERROR_IRQ_STAT = 1<<17 # General error IRQ
# _LPCD_IRQ_STAT          = 1<<19 # LPCD Detection IRQ


class PN5180:
    def __init__(self, bus, device, nns_pin, busy_pin, rst_pin, irq_pin,  protocol='ISO15693'):
        # 11.4.1 Physical Host Interface
        # The interface of the PN5180 to a host microcontroller is based on a SPI interface,
        # extended by signal line BUSY. The maximum SPI speed is 7 Mbps and fixed to CPOL = 0 and CPHA = 0.
        self._spi = spidev.SpiDev()
        self._spi.open(bus, device)
        self._spi.max_speed_hz = 50000
        self._spi.mode = 0b00
        self._spi.no_cs = True

        self._PN5180_NSS = nns_pin   # active low
        self._PN5180_BUSY = busy_pin
        self._PN5180_RST = rst_pin
        self._PN5180_IRQ = irq_pin
        self._protocol = protocol

        self.command_timeout = 50

    def begin(self):
        # Reffering to the pins Broadcom SoC
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._PN5180_NSS, GPIO.OUT)    # Chip Select Pin
        GPIO.setup(self._PN5180_BUSY, GPIO.IN)    # Busy Pin
        GPIO.setup(self._PN5180_RST, GPIO.OUT)    # Reset Pin

        GPIO.output(self._PN5180_NSS, GPIO.HIGH)  # Disable
        GPIO.output(self._PN5180_RST, GPIO.HIGH)  # No Reset

    def reset(self):
        #print ("I am Reset function :-)")   
        GPIO.output(self._PN5180_RST, GPIO.LOW)   # At least 10us required
        time.sleep(.01)                           # 10ms delay
        GPIO.output(self._PN5180_RST, GPIO.HIGH)      # 2ms to ramp up required
        time.sleep(.01)
        
        while (0 == (_IDLE_IRQ_STAT and self.get_irq_status())):            
            pass  # Wait for system to start up

        self.clear_irq_status(0xffffffff)  # Clear all flags

    def get_irq_status(self):
        irq_status = []
        self.read_register(regs._IRQ_STATUS, irq_status)
        byte_string = bytes(sum(irq_status, [])[::-1]) # Flatt list into one. Reverse list order and convert to byte string.
        return int.from_bytes(byte_string, byteorder='big') # Byte string into integer.

    def clear_irq_status(self, irq_mask: int):
        return self.write_register(regs._IRQ_CLEAR, irq_mask)

    def get_transceive_state(self):
        #print("Get Transceive state...\n")

        rf_status = []
        if (not self.read_register(regs._RF_STATUS, rf_status)):
            print('Error reading RF_STATUS register.\n')
            return PN5180_Transceive_Stat(0)

        '''PN5180_Transceive_Stat:
            0 - idle
            1 - wait transmit
            2 - transmitting
            3 - wait receive
            4 - wait for data
            5 - receiving
            6 - loopback
            7 - reserved'''
        
        # Convert list to integer
        rf_status = bytes(sum(rf_status, [])[::-1])
        rf_status_int = int.from_bytes(rf_status, byteorder='big')

        state = ((rf_status_int >> 24) & 0x07)
        #print("STATE----> ", state)
        return PN5180_Transceive_Stat(state)
        

    def write_register(self, reg: int, value: list):
        '''WRITE_REGISTER - 0x00
        This command is used to write a 32-bit value (little endian) to a configuration register.
        The address of the register mus exist. If the condition is not fulfilled, an exception is
        raised.'''

        cmd = [_PN5180_WRITE_REGISTER, reg]
        value = list((value).to_bytes(4, byteorder='little'))
        cmd += value  # Give list of bytes
        self.transceive_command(cmd, [], 0)
        return True

    def write_register_with_or_mask(self, reg, mask):
        '''WRITE_REGISTER_OR_MASK - 0x01
        This command modifies the content of a register using a logical OR operation. The content of the
        register is read and logical OR operation is performed with the provided mask. The modified content
        is written back to the register.
        The address of the register must exist. If the condition is not fulfilled, an exception is raised.'''

        buf = [_PN5180_WRITE_REGISTER_OR_MASK, reg]
        mask = list(mask.to_bytes(4, byteorder='little'))
        buf += mask
        self.transceive_command(buf, [], 0)
        return True      

    def write_register_with_and_mask(self, reg, mask):
        '''WRITE_REGISTER_AND_MASK - 0x02
        This command modifies the content of a register using a logical AND operation. The content of the
        register is read and logical AND operation is performed with the provided mask. The modified content
        is written back to the register.
        The address of the register must exist. If the condition is not fulfilled, an exception is raised.'''

        buf = [_PN5180_WRITE_REGISTER_AND_MASK, reg]
        mask = list(mask.to_bytes(4, byteorder='little'))
        buf += mask
        self.transceive_command(buf, [], 0)
        return True


    def read_register(self, reg: int, value: list):
        '''READ_REGISTER - 0x04
        This command is used to read the content of a configuration register. The content of the register
        is returnet in the 4 byte response. The address of the register must exist. If the condition is not
        fulfielled, an exception is raised.'''
        
        cmd = [_PN5180_READ_REGISTER, reg]
        self.transceive_command(cmd, value, 4)
        return True

    def transceive_command(self, send_buffer: list, recv_buffer: list, recv_buffer_len: int):
        '''A Host Interface Command consist of either 1 or 2 SPI frames depending whether the host wants to 
        write or read data from PN5180. An SPI Frame consist of multiple bytes.

        All commands are packed into one SPI Frame. An SPI Frame consists of multiple bytes. 

        No NSS toggles allowed during sending of an SPI frame.

        For all 4 byte command parameter transfers (e.g. register values), the payload parameters passed follow
        the little endia approach (Least Significant Byte first). The BUSY line is use to indicate that the system
        is BUSY line handling by the host:
          1. Assert NSS to Low
          2. Performe Data Exchange
          3. Wait until BUSY is high
          4. Deassert NSS
          5. Wait until BUSY is low
        If there is a parameter error, the IRQ is set to ACTIVE and a GENERAL_ERROR_IRQ is set'''
       
        # 0.
        started_waiting = time.time()
        while (GPIO.LOW != GPIO.input(self._PN5180_BUSY)):  # Wait until busy is low
            if (time.time() - started_waiting > self.command_timeout):
                return False
        # 1.
        GPIO.output(self._PN5180_NSS, GPIO.LOW)
        time.sleep(.002)
        # 2.
        self._spi.writebytes(send_buffer)
        ###print("Write_SPI: ", send_buffer)
        # 3.        
        started_waiting = time.time()
        while (GPIO.HIGH != GPIO.input(self._PN5180_BUSY)):  # Wait until busy is high
            if (time.time() - started_waiting > self.command_timeout):
                return False
        
        # 4.
        GPIO.output(self._PN5180_NSS, GPIO.HIGH)
        time.sleep(.001)
        # 5.
        started_waiting = time.time()
        while (GPIO.LOW != GPIO.input(self._PN5180_BUSY)):  # Wait until busy is low
            if (time.time() - started_waiting > self.command_timeout):
                return False
        
        # Check, if write-only
        if (not recv_buffer) and (not recv_buffer_len):
            return True
        #print("Receiving SPI frame...\n")

        # 1.
        GPIO.output(self._PN5180_NSS, GPIO.LOW)
        time.sleep(.002)
        # 2.
        data = self._spi.readbytes(recv_buffer_len)
        ###print("Read_SPI: ", data)
        recv_buffer.append(data)
        #print("Type recv_buffer: ", type(recv_buffer))
        #print("Type data: ", type(data))
        #recv_buffer.append(self._spi.readbytes(recv_buffer_len))
        # 3.
        started_waiting = time.time()
        while (GPIO.HIGH != GPIO.input(self._PN5180_BUSY)):  # Wait until busy is high
            if(time.time() - started_waiting > self.command_timeout):
                return False
        # 4.
        GPIO.output(self._PN5180_NSS, GPIO.HIGH)
        time.sleep(.001)
        # 5.
        started_waiting = time.time()
        while (GPIO.LOW != GPIO.input(self._PN5180_BUSY)):  # Wait until busy is low
            if(time.time() - started_waiting > self.command_timeout):
                return False

        return True

    def read_eeprom(self, addr: int, buffer: list, len: int):
        '''READ_EEPROM - 0x07
        This command is used to read data from EEPROM memory area. The field 'Address'
        indicates the start address of the read operation. The field Length indicates the number
        of bytes to read. The response contains the data read from EEPROM (content of the EEPROM);
        The data ise read in sequentially increasing order starting with the given address.

        EEpROM Address must be in the range from 0 to 254, inclusive. Read operation must not go
        beyonf EEPROM address 254. If the confition is not fulfielled, an exceprion is raised.'''

        if ((addr > 254) or ((addr + len) > 254)):
            print("ERROR: Reading beyond addr 254!\n")
            return False

        cmd = [_PN5180_READ_EEPROM, addr, len]        
        self.transceive_command(cmd, buffer, len)

        return True
    
    def send_data(self, data, len, valid_bits):
        '''SEND_DATA - 0x09
        This command writes data to the RF transmission buffer and starts the RF transmission.
        The parameter 'Number of valid bits in last Byte' indicates the exact number of bits to be
        transmitted for the last byte (for non-byte aligned frames).
        Precondition: Host shall configure the Transceiver by setting the register
        SYSTEM_CONFIG.COMMAND to 0x3 before using the SEND_DATA command, as the command SEND_DATA
        is only writing data to the transmission buffer and starts the transmission but does not perform
        any configuration.
        The size of 'Tx Data' field must be in the range from 0 to 260, inclusive (the 0 byte length allows
        a symbol only transmission when the TX_DATA_ENABLE is cleared). 'Number of valid bits in last Byte'
        field must be in the range from 0 to 7. The command must not be called during an ongoing RF 
        transmission. Transceiver must be in 'Wait Transmit' state with 'Transceive' command set. 
        If the condition is not fulfielled, an exception is raised. 
        '''

        if (len > 260):
            print("ERROR: send_data with more than 260 bytes is not supported!\n")
            return False

        buffer = [None] * (len + 2)
        buffer[0] = _PN5180_SEND_DATA
        buffer[1] = valid_bits # Number of valid bits of last byte are transmitted (0 = all bits are transmitted)
        
        for i in range(len):
            buffer[i+2] = data[i]
            
        self.write_register_with_and_mask(regs._SYSTEM_CONFIG, 0xfffffff8) # Idle/StopCom Command
        self.write_register_with_or_mask(regs._SYSTEM_CONFIG, 0x00000003)  # Transceive Command
        
        '''Transceive command; initiates a transceive cycle.
        Note: Depending on the value of the Initiator bit, a transmission is started or the receiver is
        enabled.
        Note: The transceive command does not finish automatically. It stays in the transceive cycle
        until stopped via the IDLE/StopCom command.'''

        transceive_state = self.get_transceive_state()

        if (PN5180_Transceive_Stat.PN5180_TS_WaitTransmit != transceive_state):
            print("*** ERROR: Transceiver not in state WaitTransmit!?\n")
            return False

        success = self.transceive_command(buffer, [], 0)
        return success

    def read_data(self, len, buffer):
        '''READ_DATA - 0x0A
        This command reads data from the RF reception buffer, after a successful reception.
        The RX_STATUS register contains the information to verify if the reception had been 
        successsful. The data is available within the response of the command. The host controls
        nthe number of bytes to be read via the SPI interface.
        The RF data had been successfully received. In case the instruction is executed without
        preceding an RF data reception, no exception is raised but the data read back from the
        reception buffer is invalid. If the confition is not fulfielled, and exception is raised'''
        
        if (len > 508):
            print("*** FATAL: Reading more than 508 bytes is not supported!")
            return False

        cmd = [_PN5180_READ_DATA, 0x00]
        success = self.transceive_command(cmd, buffer, len)
        return success

    # def read_data(self, len):
    #     pass

    def load_rf_config(self, tx_conf, rx_conf):
        '''LOAD_RF_CONFIG - 0x11
        Parameter 'Transmiter Configuration must be in the range from 0x0 - 0x1C, inclusive.
        If the transmitter parameter is -xFF, transmitter configuration is not changed.
        Field 'Receiver Configuration' must be in the range from 0x80 - 0x9C, inclusive.
        If the reveiver parameter is 0xFF, the receiver configuration is not changed. If the
        confition is not fulfielled, an exception is raised.

        The transmitter and receiver configuration shall always be configured for the same
        transmission/reception speed. No error is returned in case this condition is not take
        into account

        Transmitter RF    Protocol          Speed         Receiver: RF      Protocol    Speed
        configuration                       (kbit/s)      configuration                 (kbit/s)
        byte (hex)                                        byte (hex)    
        ----------------------------------------------------------------------------------------
        ->0D              ISO 15693 ASK100  26            8D                ISO 15693   26
          0E              ISO 15693 ASK10   26            8E                ISO 15693   53   '''

        cmd = [_PN5180_LOAD_RF_CONFIG, tx_conf, rx_conf]
        self.transceive_command(cmd, [], 0)

        return True

    def set_rf_on(self):
        '''RF_ON - 0x16
        This command is ised to switch on the internal RF field. If enabled the TX_RFON_IRQ is set
        after the field is switched on.'''

        cmd = [_PN5180_RF_ON, 0x00]
        self.transceive_command(cmd, [], 0)

        while (0 == (_TX_RFON_IRQ_STAT & self.get_irq_status())):
            pass  # Wait for RF Field to set up
        self.clear_irq_status(_TX_RFON_IRQ_STAT)
        return True
