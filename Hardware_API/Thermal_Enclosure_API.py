# This File will contain a class for the Thermal enclosure for NVAR box used to keep the Optics stable
#
# The class will contain the following functions:
#   - get_temperature
#   - set_temperature
#   - connect
#   - disconnect
# The Thermal Enclosure Communicates over Modbus TCP/IP
# The IP address is 
# The port is 

import minimalmodbus
import time
import datetime
import os
import numpy as np


class Thermal_Enclosure:
    def __init__(self, ip_address='192.168.1.1', port=502):
        self.ip_address = ip_address
        self.port = port
        self.instrument = minimalmodbus.Instrument(self.ip_address, 1, mode='rtu')
        self.instrument.serial.baudrate = 9600
        self.instrument.serial.bytesize = 8
        self.instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
        self.instrument.serial.stopbits = 1
        self.instrument.serial.timeout = 0.05
        self.instrument.address = 1
        self.instrument.mode = minimalmodbus.MODE_RTU
        self.instrument.debug = False
        self.instrument.close_port_after_each_call = True
        self.instrument.clear_buffers_before_each_transaction = True
        self.instrument.handle_local_echo = False

    def connect(self):
        self.instrument.serial.open()
        return
    
    def disconnect(self):
        self.instrument.serial.close()
        return
    
    def get_temperature(self):
        return self.instrument.read_register(0, 1)
    
    def set_temperature(self, temperature):
        self.instrument.write_register(0, temperature, 1)
        return
    
    def get_info(self):
        return f"Thermal Enclosure: {self.ip_address}:{self.port}"
    