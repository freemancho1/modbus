from datetime import datetime
from pymodbus.client.sync import ModbusTcpClient as ModbusClient

client = ModbusClient('localhost', port=5021)

if client.connect():

    address, count, unit = 30100, 3, 1
    s = datetime.now()
    r1 = client.read_input_registers(address, count, unit=1)
    print(f'{address}: {r1.registers}')

    address, count, unit = 30200, 3, 1
    r2 = client.read_input_registers(address, count, unit=1)
    print(f'{address}: {r2.registers}')
    print(f'processing time: {datetime.now()-s}')

    address, count, unit = 40100, 3, 1
    s = datetime.now()
    r = client.read_holding_registers(address=address, count=count, unit=unit)
    print(f'{address}: {r.registers}')
    print(f'processing time: {datetime.now()-s}')
    input()

    address, values, unit = 40100, [21, 67, 10], 1
    print(f'write_registers(address={address}, values={values}, unit={unit})')
    s = datetime.now()
    r = client.write_registers(address=address, values=values, unit=unit)
    print(f'processing time: {datetime.now()-s}')
    input()

    address, values, unit = 40100, [21, 30, 10], 1
    print(f'write_registers(address={address}, values={values}, unit={unit})')
    s = datetime.now()
    r = client.write_registers(address=address, values=values, unit=unit)
    print(f'processing time: {datetime.now()-s}')
    input()

    address, count, unit = 30100, 3, 1
    s = datetime.now()
    r1 = client.read_input_registers(address, count, unit=unit)
    print(f'{address}: {r1.registers}')

    address, count, unit = 30200, 3, 1
    r2 = client.read_input_registers(address, count, unit=unit)
    print(f'{address}: {r2.registers}')
    print(f'processing time: {datetime.now()-s}')

    address, count, unit = 40100, 3, 1
    s = datetime.now()
    r = client.read_holding_registers(address=address, count=count, unit=unit)
    print(f'{address}: {r.registers}')
    print(f'processing time: {datetime.now()-s}')
    input()

    address, count, unit = 30100, 3, 0
    s = datetime.now()
    r1 = client.read_input_registers(address, count, unit=unit)
    print(f'{address}: {r1.registers}')

    client.close()