#!/home/freeman/anaconda3/envs/modbus/bin/python
import os, sys
sys.path.append(os.path.abspath(
    os.path.join(os.path.expanduser('~'), 'projects/modbus')))

from utils.sys_options import InspectionParameters
from slave_engine import ModbusSlaveEngine


try:
    sys_params = InspectionParameters()
    if not sys_params.display_log:
        print(f'device={sys_params.device_info["type"]}, '
              f'host={sys_params.device_info["host"]}, port={sys_params.device_info["port"]}, '
              f'unit={sys_params.device_info["unit_count"]} 디바이스 실행중....')
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
