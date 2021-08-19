from pymodbus.client.sync import ModbusTcpClient as ModbusClient

client = ModbusClient('localhost', port=5020)

if client.connect():
    print('통신을 시작합니다.')
    _ = input()

    address, value, count, unit = 10, None, 10, 5

    print(f'read_holding_registers(address={address}, count={count}) # unit=0')
    r = client.read_input_registers(address, count=count)
    print(f'get data size({len(r.registers)}), data={r.registers}')
    _ = input()

    print(f'read_holding_registers(address={address}, count={count}, unit={unit})')
    r = client.read_input_registers(address, count=count, unit=unit)
    print(f'get data size({len(r.registers)}), data={r.registers}')
    _ = input()