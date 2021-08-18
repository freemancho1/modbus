from pymodbus.client.sync import ModbusTcpClient as ModbusClient

client = ModbusClient('localhost', port=5020)

if client.connect():
    print('통신을 시작합니다.')
    _ = input()

    print('write_coil(0, True)')
    result = client.write_coil(address=0, value=True, unit=0)
    _ = input()

    print('read_coils(0, 1)')
    result = client.read_coils(address=0, count=1)
    print(result.bits[0])
    _ = input()

    print('write_coil(0, False)')
    result = client.write_coil(address=0, value=0, unit=0)
    _ = input()

    print('read_coils(0, count=1)')
    result = client.read_coils(address=0, count=1, unit=0)
    print(result.bits[0])
    _ = input()

    print('write_coils(1, [True]*8)')
    result = client.write_coils(address=0, values=[True]*8)
    _ = input()

    print('read_coils(1, 21)')
    result = client.read_coils(address=0, count=21)
    print(result.bits)
    _ = input()

    print('write_coils(1, [1,1,0,0], unit=1)')
    result = client.write_coils(address=1, values=[1,1,0,0], unit=1)

    print('read_coils(0, 21, unit=1)')
    result = client.read_coils(address=0, count=21, unit=1)
    print(result.bits)

    client.close()
