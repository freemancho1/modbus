from pymodbus.client.sync import ModbusTcpClient as ModbusClient

client = ModbusClient('localhost', port=5021)

if client.connect():

    addr, values, unit = 15, [1,1,1], 1
    print(f'write_coils(addr={addr}, values={values}, unit={unit})')
    r6 = client.write_coils(address=addr, values=values, unit=unit)
    input()

    addr, values, unit = 15, [1,0,0,0], 1
    print(f'write_coils(addr={addr}, values={values}, unit={unit})')
    r6 = client.write_coils(address=addr, values=values, unit=unit)
    input()

    addr, values, unit = 15, [0,0,1], 1
    print(f'write_coils(addr={addr}, values={values}, unit={unit})')
    r6 = client.write_coils(address=addr, values=values, unit=unit)
    input()

    addr, count, unit = 15, 3, 1
    print(f'read_coils(addr={addr}, count={count}, unit={unit})')
    r7 = client.read_coils(address=addr, count=count, unit=unit)
    print(r7.bits)
    input()

    addr, count, unit = 10015, 3, 1
    print(f'read_discrete_inputs(address={addr}, count={count}, unit={unit})')
    r8 = client.read_discrete_inputs(address=addr, count=count, unit=unit)
    print(r8.bits)
    input()

    addr, count, unit = 15, 3, 2
    print(f'read_coils(addr={addr}, count={count}, unit={unit})')
    r7 = client.read_coils(address=addr, count=count, unit=unit)
    print(r7.bits)
    addr, count, unit = 10015, 3, 2
    print(f'read_discrete_inputs(address={addr}, count={count}, unit={unit})')
    r8 = client.read_discrete_inputs(address=addr, count=count, unit=unit)
    print(r8.bits)