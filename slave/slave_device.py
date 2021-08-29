#!/home/freeman/anaconda3/envs/modbus/bin/python
import os, sys
sys.path.append(os.path.abspath(
    os.path.join(os.path.expanduser('~'), 'projects/modbus')))

from slave_options import InspectionParameters
from slave_engine import ModbusSlaveEngine


try:
    sys_params = InspectionParameters()
except Exception as e:
    print(f'Error: {str(e)}')
    sys.exit()

modbus_simulator = None
try:
    modbus_simulator = ModbusSlaveEngine(sys_params.get_params())
    modbus_simulator.start()
except:
    pass
finally:
    # 정상적으로 ModbusSlaveEngine이 만들어지 경우에만, 종료시킴
    if isinstance(modbus_simulator, ModbusSlaveEngine):
        modbus_simulator.stop()

