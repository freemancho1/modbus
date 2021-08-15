import os, sys
sys.path.append(os.path.abspath(__file__+'/../..'))

from utils.logs.logger import Logger
from utils.sys_options import SysOptions
from log_test_sub import log_sub
import time

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

    sys_parser = SysOptions()
    sys_options = sys_parser.get_options()
    log.set_config(f'{sys_options.host}:{sys_options.port}',
                   sys_options.log_level, sys_options.display_log)

    while True:
        try:
            log.debug('ccccc')
            log_test()
            time.sleep(2)
        except:
            sys.exit()
