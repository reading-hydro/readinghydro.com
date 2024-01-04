import pymodbus
from pymodbus.pdu import ModbusRequest
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
#initialize a serial RTU client instance
from pymodbus.transaction import ModbusRtuFramer

# count= the number of registers to read
# unit= the slave unit this request is targeting
# address= the starting address to read from
address = [{'addr': 0x0618, 'text': 'Total Energy'},
           {'addr': 0x0800, 'text': 'Import Active Energy'},
           {'addr': 0x0900, 'text': 'Export Active Energy'}]


def main():

    client = ModbusClient(method='rtu', port='/dev/ttyUSB0', baudrate=9600)

    # Connect to the serial modbus server
    connection = client.connect()
    if connection:
        for reg in address:
            read = client.read_holding_registers(address=reg.addr, count=4, unit=1)
            data = read.registers
            print(data, reg.text)

    # Closes the underlying socket connection
    client.close()


if __name__ == '__main__':
    main()
