#!/home/freeman/anaconda3/envs/modbus/bin/python
import os, sys
# sys.path.append(os.path.abspath(__file__+'/../..'))
sys.path.append(os.path.abspath(
    os.path.join(os.path.expanduser('~'), 'projects/modbus')))

from utils.sys_options import InspectionParameters
from slave_engine import ModbusSlaveEngine


try:
    sys_params = InspectionParameters()
    if not sys_params.display_log:
        print(f'{sys_params.host}:{sys_params.port} '
              f'[{sys_params.device_type}] 디바이스 실행중....')
except Exception as e:
    print(f'에러: {str(e)}')
    sys.exit()

modbus_simulator = None
try:
    modbus_simulator = ModbusSlaveEngine(sys_params)
    modbus_simulator.start()
except:
    sys.exit()
finally:
    modbus_simulator.stop()
