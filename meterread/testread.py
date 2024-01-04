import pymodbus
from pymodbus.pdu import ModbusRequest
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
#initialize a serial RTU client instance
from pymodbus.transaction import ModbusRtuFramer

# count= the number of registers to read
# unit= the slave unit this request is targeting
# address= the starting address to read from
address = [{'addr': 0x0618, 'text': 'Total Energy'},
           {'addr': 0x0160, 'text': 'Export'},
           {'addr': 0x0166, 'text': 'Import'},
           {'addr': 0x0800, 'text': 'Import Active Energy'},
           {'addr': 0x0900, 'text': 'Export Active Energy'},
           {'addr': 0x0010, 'text': 'Voltage P1'},
           {'addr': 0x0012, 'text': 'Voltage P2'},
           {'addr': 0x0014, 'text': 'Voltage P3'},
           {'addr': 0x0050, 'text': 'Current P1'},
           {'addr': 0x0052, 'text': 'Current P2'},
           {'addr': 0x0054, 'text': 'Current P3'}]

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
