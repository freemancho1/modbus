from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from datetime import datetime

client = ModbusClient('localhost', port=5021)

if client.connect():

    # # addr, value, unit = 100, False, 1   # 값이 0,1이 아닌 5를 넣은 경우 테스트(0/False 아니면 모두 True)
    # addr, value, unit = 15, 1, 1
    # print(f'write_coil(addr={addr}, value={value}, unit={unit})')
    # s = datetime.now()
    # r1 = client.write_coil(address=addr, value=value, unit=unit)
    # print(f'processing time: {datetime.now()-s}')
    # _ = input()

    # addr, value, unit = 17, 1, 1
    # print(f'write_coil(addr={addr}, value={value}, unit={unit})')
    # s = datetime.now()
    # r2 = client.write_coil(address=addr, value=value, unit=unit)
    # print(f'processing time: {datetime.now()-s}')
    # _ = input()

    # addr, count, unit = 15, 3, 1
    # print(f'read_coils(addr={addr}, count={count}, unit={unit})')
    # s = datetime.now()
    # r3 = client.read_coils(address=addr, count=count, unit=unit)
    # print(f'processing time: {datetime.now() - s}')
    # print(r3.bits)
    # _ = input()
    #
    # addr, value, unit = 102, False, 1
    # print(f'write_coil(addr={addr}, value={value}, unit={unit})')
    # s = datetime.now()
    # r4 = client.write_coil(address=addr, value=value, unit=unit)
    # print(f'processing time: {datetime.now()-s}')
    # addr, count, unit = 100, 5, 1
    # print(f'read_coils(addr={addr}, count={count}, unit={unit})')
    # r5 = client.read_coils(address=addr, count=count, unit=unit)
    # print(r5.bits)
    # _ = input()

    addr, values, unit = 15, [1,1,1], 1
    print(f'write_coils(addr={addr}, values={values}, unit={unit})')
    r6 = client.write_coils(address=addr, values=values, unit=unit)

    addr, count, unit = 15, 3, 1
    print(f'read_coils(addr={addr}, count={count}, unit={unit})')
    r7 = client.read_coils(address=addr, count=count, unit=unit)
    print(r7.bits)

    # addr, values, unit = 103, [0,1,1,0], 1
    # print(f'write_coils(addr={addr}, values={values}, unit={unit})')
    # r8 = client.write_coils(address=addr, values=values, unit=unit)
    # _ = input()
    #
    # addr, count, unit = 100, 10, 1
    # print(f'read_coils(addr={addr}, count={count}, unit={unit})')
    # r9 = client.read_coils(address=addr, count=count, unit=unit)
    # print(r9.bits)
    # _ = input()

    client.close()
