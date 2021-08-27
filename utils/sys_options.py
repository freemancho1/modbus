import os
import sys
import json
import socket
from optparse import OptionParser

from utils.logs import config as LOG_CONF
from . import sys_config as SYS_CONF
from slave.slave_utils import DevInfo


class InputParameters:

    def __init__(self):
        self._parser = OptionParser()
        self._parser.add_option('-H', '--host', dest='host',
                                default='127.0.0.1',
                                help='디바이스 IP 정보, 필수항목(기본값: 127.0.0.1).')
        self._parser.add_option('-P', '--port', dest='port', type=int,
                                default=0, help='디바이스 PORT 정보, 필수항목.')
        self._parser.add_option('-U', '--unit-count', dest='unit_cnt',
                                default=1, type=int,
                                help='디바이스 유닛 갯 수, 필수항목(기본값: 1).')
        self._parser.add_option('-I', '--device-info', dest='dev_info',
                                default='', help='디바이스 설정파일 정보, 필수항목.')
        self._parser.add_option('-N', '--no-display', dest='no_disp',
                                default=True, action='store_false',
                                help='디바이스 정보 출력 여부 설정, 기본값 \'표시하지 않음\'')
        self._parser.add_option('-L', '--log-level', dest='log_level',
                                default=LOG_CONF.DEFAULT_LEVEL, type=str,
                                help=f'''로그 출력 레벨을 설정한다. 기본값은 '{LOG_CONF.DEFAULT_LEVEL}'.
                                     debug, info, warning, error, critical을 사용할 수 있음.''')
        (self._options, self._args) = self._parser.parse_args()

    def get_options(self):
        return self._options

    def get_agrs(self):
        return self._args

    def print_help(self):
        self._parser.print_help()


class InspectionParameters:

    def __init__(self):
        self.soc_params = InputParameters()
        self.soc_opts = self.soc_params.get_options()
        self.soc_args = self.soc_params.get_agrs()
        self.dev_info = DevInfo()
        try:
            self._inspect_input()
        except Exception as e:
            raise Exception(str(e))

    def _inspect_input(self):
        _file = self.soc_opts.dev_info if len(self.soc_opts.dev_info) > 0 else ''

        if len(_file) == 0:
            self.soc_params.print_help()
            raise Exception(f'디바이스 설정파일을 입력하세요. 필수항목입니다.')

        _dev_file = os.path.join(SYS_CONF.DEVICE_INFO_PATH, f'{_file}.json')
        if not os.path.exists(_dev_file):
            raise Exception(f'지정한 디바이스 설정파일을 찾을 수 없습니다. '
                            f'파일명: {_dev_file}')

        _host = self.soc_opts.host
        _port = self.soc_opts.port
        _socket = None
        try:
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _socket.bind((_host, _port))
        except Exception as e:
            raise Exception(f'지정한 IP와 포트번호를 사용할 수 없습니다. '
                            f'host:port={_host}:{_port}\n{str(e)}')
        else:
            self.dev_info.host, self.dev_info.port = _host, _port
            self.type = _file
            self.dev_info.unit_cnt = min(self.soc_opts.unit_cnt, SYS_CONF.MAX_UNIT_CNT)
        finally:
            if isinstance(_socket, socket.socket):
                _socket.close()

        _level = self.soc_opts.log_level
        if hasattr(LOG_CONF.LEVEL, _level):
            self.dev_info.log_level = _level
        else:
            raise Exception(f'표시할 로그레벨 설정값을 잘못 입력했습니다. '
                            f'입력한 로그레벨: {_level}')

        self.no_disp = self.soc_opts.no_disp        # True = No Display

        def _get_data(_soc_data):
            if _soc_data is None:
                _addr = [0, 0]
                _data = []
            else:
                _addr = [_soc_data.get('start_addr', 0), _soc_data.get('end_addr', 0)]
                _data = _soc_data.get('data', [])
            self.dev_info.addr.append(_addr)
            self.dev_info.data.append(_data)

        try:
            with open(_dev_file, encoding='utf-8') as dif:
                _cfg = json.load(dif)

                _drv_type = _cfg['device_driver']
                _drv_file = os.path.join(SYS_CONF.DRIVER_FULL_PATH, f'{_drv_type}.py')
                if not os.path.exists(_drv_file):
                    raise Exception(f'지정한 드라이브 파일을 찾을 수 없습니다. '
                                    f'파일명: {_drv_file}')

                self.dev_info.drv = _drv_type
                self.dev_info.itv = _cfg.get('generation_interval', 1)

                _get_data(_cfg.get('coil', None))
                _get_data(_cfg.get('discrete_input', None))
                _get_data(_cfg.get('input_register', None))
                _get_data(_cfg.get('holding_register', None))

                # 실제 주소계산(입력주소값-메모리시작주소값=실제메모리주소값)을 위해 기본메모리값 저장
                self.dev_info.w_addr = self.dev_info.addr[2][0]
                for i in range(len(self.dev_info.addr)):
                    self.dev_info.addr[i].append(
                        self.dev_info.addr[0][0] if i < 2 else self.dev_info.w_addr)

        except Exception as e:
            raise Exception(f'제품 정보파일을 처리하는 과정에서 에러가 발생했습니다. '
                            f'파일명: {_dev_file}\n{str(e)}')

    def get_params(self):
        return self.dev_info