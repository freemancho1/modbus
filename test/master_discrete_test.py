from pymodbus.client.sync import ModbusTcpClient as ModbusClient

client = ModbusClient('localhost', port=5020)

if client.connect():
    print('통신을 시작합니다.')
    _ = input()

    print('read_discrete_inputs(0, 4)')
    r = client.read_discrete_inputs(0, 9, unit=1)
    print(r.bits)
