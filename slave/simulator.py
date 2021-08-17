import os, sys
sys.path.append(os.path.abspath(__file__+'/../..'))

from utils.sys_options import InspectionParameters
from slave_engine import ModbusSlaveEngine

try:
    sys_params = InspectionParameters()
except Exception as e:
    print(f'에러: {str(e)}')
    sys.exit()

try:
    server = ModbusSlaveEngine(sys_params)
    server.start()
except:
    server.stop()
