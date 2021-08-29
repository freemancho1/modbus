import os, sys
sys.path.append(os.path.abspath(__file__+'/../..'))

from utils.logs.logger import Logger
from slave.slave_options import InspectionParameters
from log_test_sub import log_sub

log = Logger()

class MyClass:
    pass


def log_xx():
    log.info('bbbb')
    log_sub(log)

def log_test():
    log.warning('aaaaa')
    log_xx()

if __name__ == '__main__':

    try:
        sys_options = InspectionParameters()
        log.set_config(f'{sys_options.host}:{sys_options.port}',
                       sys_options.log_level, sys_options.display_log)
        log_test()
    except Exception as e:
        print(f'에러: {str(e)}')
        sys.exit()
