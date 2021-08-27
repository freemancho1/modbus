#!/home/freeman/anaconda3/envs/modbus/bin/python
import os, sys
sys.path.append(os.path.abspath(
    os.path.join(os.path.expanduser('~'), 'projects/modbus')))

from utils.sys_options import InspectionParameters
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
    sys.exit()
finally:
    modbus_simulator.stop()

