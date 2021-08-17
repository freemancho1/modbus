from pymodbus.client.sync import ModbusTcpClient as ModbusClient

client = ModbusClient('localhost', port=5020)

if client.connect():
    _ = input()

    result = client.write_coil(address=0, value=10)
    print(result)
    _ = input()


    client.close()