from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from datetime import datetime

client = ModbusClient('localhost', port=5021)

if client.connect():

    addr, count = 15, 4
    for i in range(5):
        s = datetime.now()
        r = client.read_coils(addr, count, unit=i)
        print(f'processing time: {datetime.now()-s}')
        print(f'unit_id({i}): {r.bits}')

    addr, count = 10011, 8
    for i in range(5):
        s = datetime.now()
        r = client.read_discrete_inputs(addr, count, unit=i)
        print(f'processing time: {datetime.now()-s}')
        print(f'unit_id({i}): {r.bits}')

    addr, count = 30100, 4
    for i in range(5):
        s = datetime.now()
        r = client.read_input_registers(addr, count, unit=i)
        print(f'processing time: {datetime.now()-s}')
        print(f'unit_id({i}): {r.registers}')

    addr, count = 40100, 4
    for i in range(5):
        s = datetime.now()
        r = client.read_holding_registers(addr, count, unit=i)
        print(f'processing time: {datetime.now()-s}')
        print(f'unit_id({i}): {r.registers}')