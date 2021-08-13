import os, sys
sys.path.append(os.path.abspath(__file__+'/../..'))

from utils.logs.logger import Logger
from utils.sys_options import SysOptions


if __name__ == '__main__':

    sys_parser = SysOptions()
    sys_options = sys_parser.get_options()
    print(sys_options)
    print(sys_parser.get_agrs())

