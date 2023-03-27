#! /usr/bin/python3

import sys
import datetime
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

REG_EXPORT = 0x0160
REG_IMPORT = 0x0166
MTR = "OB737"

#address = [{'addr': 0x0160, 'text': 'Export'},
#           {'addr': 0x0166, 'text': 'Import'}]
#           {'addr': 0x0010, 'text': 'Voltage P1'},
#           {'addr': 0x0012, 'text': 'Voltage P2'},
#           {'addr': 0x0014, 'text': 'Voltage P3'},
#           {'addr': 0x0050, 'text': 'Current P1'},
#           {'addr': 0x0052, 'text': 'Current P2'},
#           {'addr': 0x0054, 'text': 'Current P3'}]

jsonstring = '"datetime":"{isodate}","meter":"{meter}","import":{rimport},"export":{rexport}'

def main():

    client = ModbusClient(method='rtu', port='/dev/ttyUSB0', baudrate=9600)

    # Connect to the serial modbus server
    connection = client.connect()
    if connection:
        tries = 3
        while tries > 0:
            try:
                read = client.read_holding_registers(address=REG_EXPORT, count=2, unit=1)
                mtrexport = read.registers[1]
            except:
                tries -=1
                print('< read error', file=sys.stderr)
            else: 
                tries = 0
                print('< export', mtrexport, file=sys.stderr)

        tries = 3
        while tries > 0:
            try:
                read = client.read_holding_registers(address=REG_IMPORT, count=2, unit=1)
                mtrimport = read.registers[1]
            except:
                tries -= 1
                print('< read error', file=sys.stderr)
            else:
                tries = 0
                print('< import ', mtrimport, file=sys.stderr)

        print('{' + jsonstring.format(isodate=datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z',
                                 meter=MTR, rimport=mtrimport, rexport=mtrexport) + '}')
        
    # Closes the underlying socket connection
    client.close()


if __name__ == '__main__':
    main()
