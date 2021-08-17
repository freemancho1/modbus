import os
import sys
import json
import socket
from optparse import OptionParser

from utils.logs import config as LOG_CONF


class InputParameters:

    def __init__(self):
        self._parser = OptionParser()
        self._parser.add_option('-I', '--device-info', dest='device_info_file_path',
                                default='', help='디바이스 정보파일을 설정한다. 필수항목입니다.')
        self._parser.add_option('-L', '--log-level', dest='log_level',
                                default=LOG_CONF.DEFAULT_LEVEL, type=str,
                                help=f'''로그 출력 레벨을 설정한다. 기본값은 '{LOG_CONF.DEFAULT_LEVEL}'이다.
                                     debug, info, warning, error, critical을 사용할 수 있다.''')
        self._parser.add_option('-D', '--no-display-log', dest='display_log',
                                action='store_false', default=LOG_CONF.DEFAULT_DISPLAY,
                                help=f'''화면에 로그 출력 여부를 설정한다. 기본값은 '{LOG_CONF.DEFAULT_DISPLAY}'이다.
                                     (이 설정은 로그의 화면 출력 여부만 설정하며, 로그파일에 영향을 주지 않는다.)''')
        self._parser.add_option('', '--block', dest='no_block',
                                default=False, action='store_true',
                                help='통신 시 데이터 블럭지정 여부를 결정한다. 기본값은 블럭지정을 하지 않는다.')
        self._parser.add_option('', '--ipv6', dest='ipv6', default=False, action='store_true',
                                help='통신 방법을 IPV6 형태로 변경해 수행한다. 기본값은 IPV4이다.')
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
        self.soc_options = self.soc_params.get_options()
        self.soc_args = self.soc_params.get_agrs()
        self.device_type = ''
        self.host = ''
        self.port = 0
        self.device_info = ''
        self.log_level = LOG_CONF.DEFAULT_LEVEL
        self.display_log = LOG_CONF.DEFAULT_DISPLAY
        self.no_block = False
        self.ipv6 = False
        self.config = None
        try:
            self._inspect_device_info()
            self._inspect_log_level()
            self._inspect_etc()
        except Exception as e:
            raise Exception(str(e))

    def __str__(self):
        return f'device type={self.device_type}, ' \
               f'host={self.host}, port={self.port}, ' \
               f'device_info_file={self.device_info}, ' \
               f'log_level={self.log_level}, display_log={self.display_log}, ' \
               f'block={self.no_block}, ipv6={self.ipv6}'

    def _inspect_device_info(self):
        # soc_options에서 값을 찾고 없으면, soc_args의 첫번째 값을 취한다.
        device_info = self.soc_options.device_info_file_path \
                      if len(self.soc_options.device_info_file_path) > 0 \
                      else self.soc_args[0] if len(self.soc_args) > 0 else ''

        if len(device_info) == 0:
            self.soc_params.print_help()
            raise Exception(f'디바이스 설정파일을 입력하세요. 필수항목입니다.')

        if not os.path.exists(device_info):
            raise Exception(f'지정한 디바이스 설정파일을 찾을 수 없습니다. 파일명: {device_info}')

        try:
            with open(device_info, encoding='utf-8') as device_info_file:
                self.config = json.load(device_info_file)
                self._inspect_config()
                self.device_info = device_info
        except Exception as e:
            raise Exception(f'설정파일을 처리하는 과정에서 에러가 발생했습니다. '
                            f'파일명: {device_info}\n{str(e)}')

    def _inspect_config(self):
        host = self.config['server']['host']
        port = self.config['server']['port']
        try:
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _socket.bind((host, port))
        except Exception as e:
            raise Exception(f'지정한 IP와 포트번호를 사용할 수 없습니다. '
                            f'host:port={host}:{port}\n{str(e)}')
        else:
            self.device_type = self.config['device_type']
            self.host, self.port = host, port
        finally:
            _socket.close()

    def _inspect_log_level(self):
        log_level = self.soc_options.log_level
        if hasattr(LOG_CONF.LEVEL, log_level):
            self.log_level = log_level
        else:
            raise Exception(f'표시할 로그레벨 설정값을 잘못 입력했습니다. '
                            f'입력한 로그레벨: {log_level}')

    def _inspect_etc(self):
        self.display_log = self.soc_options.display_log
        self.no_block = self.soc_options.no_block
        self.ipv6 = self.soc_options.ipv6