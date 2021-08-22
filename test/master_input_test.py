from datetime import datetime
from pymodbus.client.sync import ModbusTcpClient as ModbusClient

client = ModbusClient('localhost', port=5021)

if client.connect():

    address, count, unit = 30100, 3, 0
    print(f'client.read_input_registers(address={address}, count={count}, unit={unit})')
    s = datetime.now()
    r = client.read_input_registers(address=address, count=count, unit=unit)
    print(f'processing time: {datetime.now()-s}')
    print(f'get data size({len(r.registers)}), data={r.registers}')

    address, count, unit = 30900, 1, 0
    print(f'client.read_input_registers(address={address}, count={count}, unit={unit})')
    s = datetime.now()
    r = client.read_input_registers(address=address, count=count, unit=unit)
    print(f'processing time: {datetime.now()-s}')
    print(f'get data size({len(r.registers)}), data={r.registers}')
