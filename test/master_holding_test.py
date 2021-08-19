from pymodbus.client.sync import ModbusTcpClient as ModbusClient

client = ModbusClient('localhost', port=5020)

if client.connect():
    print('통신을 시작합니다.')
    _ = input()

    address, value, count, unit = 0, 11, 1, 1

    print(f'write_register(address={address}, value={value}, unit={unit})')
    r = client.write_register(address=address, value=value, unit=unit)
    print(r)
    _ = input()

    print(f'read_holding_registers(address={address}, count={count}) # unit=0')
    r = client.read_holding_registers(address, count=count)   # unit=0
    print(f'get data size({len(r.registers)}), data={r.registers}')
    _ = input()

    print(f'read_holding_registers(address={address}, count={count}, unit={unit})')
    r = client.read_holding_registers(address, count=count, unit=unit)
    print(f'get data size({len(r.registers)}), data={r.registers}')
    _ = input()

    print('Read/Write Multi Holding Register Sample')
    address, values, count, unit = 0x000A, [10, 20, 30, 40], 4, 5

    print(f'write_registers(address={address}, values={values}, unit={unit})')
    r = client.write_registers(address=address, values=values, unit=unit)
    print(r)
    _ = input()

    print(f'read_holding_registers(address={address}, count={count}, unit={unit})')
    r = client.read_holding_registers(address=address, count=count, unit=unit)
    print(f'get data size({len(r.registers)}), data={r.registers}')

    client.close()