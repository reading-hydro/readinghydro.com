import pymodbus
from pymodbus.pdu import ModbusRequest
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
#initialize a serial RTU client instance
from pymodbus.transaction import ModbusRtuFramer

#count= the number of registers to read
#unit= the slave unit this request is targeting
#address= the starting address to read from

client = ModbusClient(method = 'rtu', port = '/dev/ttyUSB0', baudrate = 9600)

#Connect to the serial modbus server
connection = client.connect()
print(connection)

#Starting add, num of reg to read, slave unit.
read = client.read_holding_registers(address = 0x0160,count = 4, unit=1)
print(read)
data = read.registers

print(data)

#Closes the underlying socket connection
client.close()