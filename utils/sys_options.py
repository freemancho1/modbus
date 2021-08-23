import os
import sys
import json
import socket
from optparse import OptionParser

from utils.logs import config as LOG_CONF
from . import sys_config as SYS_CONF


class InputParameters:

    def __init__(self):
        self._parser = OptionParser()
        self._parser.add_option('-I', '--device-info', dest='device_info_file',
                                default='', help='디바이스 정보파일을 설정한다. 필수항목입니다.')
        self._parser.add_option('-L', '--log-level', dest='log_level',
                                default=LOG_CONF.DEFAULT_LEVEL, type=str,
                                help=f'''로그 출력 레벨을 설정한다. 기본값은 '{LOG_CONF.DEFAULT_LEVEL}'이다.
                                     debug, info, warning, error, critical을 사용할 수 있다.''')
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
        self.device_info = {}
        self.product_info = {}
        self.log_level = LOG_CONF.DEFAULT_LEVEL
        self.display_log = LOG_CONF.DEFAULT_DISPLAY
        try:
            self._inspect_device_info()
            self._inspect_log_level()
        except Exception as e:
            raise Exception(str(e))

    def __str__(self):
        return f'device info={self.device_info}, ' \
               f'product info={self.product_info}, ' \
               f'log_level={self.log_level}, display_log={self.display_log}'

    def _inspect_device_info(self):
        # soc_options에서 값을 찾고 없으면, soc_args의 첫번째 값을 취한다.
        device_info_file = self.soc_options.device_info_file \
                           if len(self.soc_options.device_info_file) > 0 \
                           else self.soc_args[0] if len(self.soc_args) > 0 else ''

        if len(device_info_file) == 0:
            self.soc_params.print_help()
            raise Exception(f'디바이스 설정파일을 입력하세요. 필수항목입니다.')

        device_info_file = os.path.join(SYS_CONF.DEVICE_INFO_PATH, device_info_file)
        if not os.path.exists(device_info_file):
            raise Exception(f'지정한 디바이스 설정파일을 찾을 수 없습니다. 파일명: {device_info_file}')

        try:
            with open(device_info_file, encoding='utf-8') as dif:
                device_config = json.load(dif)
                self._inspect_config(device_config)
        except Exception as e:
            raise Exception(f'설정파일을 처리하는 과정에서 에러가 발생했습니다. '
                            f'파일명: {device_info_file}\n{str(e)}')

    def _inspect_config(self, device_config):

        product_info_file = os.path.join(SYS_CONF.DEVICE_INFO_PATH,
                                         f'{device_config["device_type"]}.json')
        if not os.path.exists(product_info_file):
            raise Exception(f'제품 설정파일을 찾을 수 없습니다. 파일명: {product_info_file}')

        try:
            with open(product_info_file, encoding='utf-8') as pif:
                product_config = json.load(pif)
                driver_file = os.path.join(SYS_CONF.DRIVER_FULL_PATH,
                                           f'{product_config["device_driver"]}.py')
                self.product_info['generation_interval'] = product_config['generation_interval']
                self.product_info['coil'] = product_config['coil']
                self.product_info['discrete_input'] = product_config['discrete_input']
                self.product_info['input_register'] = product_config['input_register']
                self.product_info['holding_register'] = product_config['holding_register']
                self.product_info['driver'] = product_config['device_driver']
        except Exception as e:
            raise Exception(f'제품 정보파일을 처리하는 과정에서 에러가 발생했습니다. '
                            f'파일명: {product_info_file}\n{str(e)}')

        if not os.path.exists(driver_file):
            raise Exception(f'드라이버 파일을 찾을 수 없습니다. 파일명: {driver_file}')

        host = device_config['server']['host']
        port = device_config['server']['port']
        try:
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _socket.bind((host, port))
        except Exception as e:
            raise Exception(f'지정한 IP와 포트번호를 사용할 수 없습니다. '
                            f'host:port={host}:{port}\n{str(e)}')
        else:
            self.device_info['type'] = device_config['device_type']
            self.device_info['host'] = host
            self.device_info['port'] = port
            _u_cnt = device_config['server']['unit_count']
            self.device_info['unit_count'] = _u_cnt if SYS_CONF.MAX_UNIT_CNT > _u_cnt \
                                                    else SYS_CONF.MAX_UNIT_CNT
        finally:
            _socket.close()

    def _inspect_log_level(self):
        log_level = self.soc_options.log_level
        if hasattr(LOG_CONF.LEVEL, log_level):
            self.log_level = log_level
        else:
            raise Exception(f'표시할 로그레벨 설정값을 잘못 입력했습니다. '
                            f'입력한 로그레벨: {log_level}')
