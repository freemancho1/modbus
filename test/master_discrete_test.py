from datetime import datetime
from pymodbus.client.sync import ModbusTcpClient as ModbusClient

client = ModbusClient('localhost', port=5021)

if client.connect():
    print('통신을 시작합니다.')
    _ = input()

    addr, count, unit = 10011, 1, 1
    print(f'read_discrete_inputs(addr={addr}, count={count}, unit={unit})')
    s = datetime.now()
    r = client.read_discrete_inputs(address=addr, count=count, unit=1)
    print(f'processing time: {datetime.now()-s}')
    print(r.bits)

    # addr, count, unit = 10200, 10, 1
    # print(f'read_discrete_inputs(addr={addr}, count={count}, unit={unit})')
    # s = datetime.now()
    # r = client.read_discrete_inputs(address=addr, count=count, unit=1)
    # print(f'processing time: {datetime.now()-s}')
    # print(r.bits)
