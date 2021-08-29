import os, sys
sys.path.append(os.path.abspath(__file__+'/../..'))

from slave.slave_options import SysOptions


if __name__ == '__main__':

    sys_parser = SysOptions()
    sys_options = sys_parser.get_options()

    print(f'system options:\n{sys_options}')
    print(f'system arguments:\n{sys_parser.get_agrs()}')

    sys_parser.print_help()
