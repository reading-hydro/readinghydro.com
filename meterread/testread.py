import pymodbus
from pymodbus.pdu import ModbusRequest
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
#initialize a serial RTU client instance
from pymodbus.transaction import ModbusRtuFramer

# count= the number of registers to read
# unit= the slave unit this request is targeting
# address= the starting address to read from
address = [{'addr': 0x0618, 'text': 'Total Energy', 'factor': 10, 'units': 'kWh'},
           {'addr': 0x0160, 'text': 'Export', 'factor': 10, 'units': 'kWh'},
           {'addr': 0x0166, 'text': 'Import', 'factor': 10, 'units': 'kWh'},
           {'addr': 0x0800, 'text': 'Export Active Energy', 'factor': 10, 'units': 'kWh'},
           {'addr': 0x0900, 'text': 'Import Active Energy', 'factor': 10, 'units': 'kWh'},
           {'addr': 0x0010, 'text': 'Voltage P1', 'factor': 1, 'units': 'V'},
           {'addr': 0x0012, 'text': 'Voltage P2', 'factor': 1, 'units': 'V'},
           {'addr': 0x0014, 'text': 'Voltage P3', 'factor': 1, 'units': 'V'},
           {'addr': 0x0050, 'text': 'Current P1', 'factor': 1, 'units': 'A'},
           {'addr': 0x0052, 'text': 'Current P2', 'factor': 1, 'units': 'A'},
           {'addr': 0x0054, 'text': 'Current P3', 'factor': 1, 'units': 'A'}]

def main():

    client = ModbusClient(method='rtu', port='/dev/ttyUSB0', baudrate=9600)

    # Connect to the serial modbus server
    connection = client.connect()
    if connection:
        for reg in address:
            try:
                read = client.read_holding_registers(address=reg.get('addr'), count=2, unit=1)
            except:
                print("Read Error <",read)
            else:
                if hasattr(read, 'registers'):
                    data = (read.registers[1] + (65536 * read.registers[0]))/reg.get('factor')
                    print(data, reg.get('units'), reg.get('text'))
                else:
                    print("Modbus error <", read)

    # Closes the underlying socket connection
    client.close()


if __name__ == '__main__':
    main()
