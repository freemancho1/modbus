from datetime import datetime
from pymodbus.client.sync import ModbusTcpClient as ModbusClient

client = ModbusClient('localhost', port=5021)

if client.connect():

    # address, value, unit = 40100, 1234, 1
    # print(f'write_register(address={address}, value={value}, unit={unit})')
    # s = datetime.now()
    # r = client.write_register(address=address, value=value, unit=unit)
    # print(f'processing time: {datetime.now()-s}')
    # print(r)
    # _ = input()
    #
    # address, value, unit = 40102, [2321, 3333, 4028, 7789], 1
    # print(f'write_registers(address={address}, values={value}, unit={unit})')
    # s = datetime.now()
    # r = client.write_registers(address=address, values=value, unit=unit)
    # print(f'processing time: {datetime.now()-s}')
    # print(r)
    # _ = input()

    address, count, unit = 40100, 3, 1
    print(f'client.read_holding_registers(address={address}, count={count}, unit={unit})')
    s = datetime.now()
    r = client.read_holding_registers(address=address, count=count, unit=unit)
    print(f'processing time: {datetime.now()-s}')
    print(f'get data size({len(r.registers)}), data={r.registers}')

    client.close()