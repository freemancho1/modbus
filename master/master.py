#!/home/freeman/anaconda3/envs/modbus/bin/python
import os
import sys
import json
import socket
sys.path.append(os.path.abspath(
    os.path.join(os.path.expanduser('~'), 'projects/modbus')))

from datetime import datetime
from optparse import OptionParser
from pymodbus.client.sync import ModbusTcpClient

from utils import sys_config

dev_info = {}


def input_parameters():

    parser = OptionParser()
    parser.add_option('-i', '--info-file', dest='info_file',
                      default='', help='디바이스 정보파일을 설정한다. 필수항목입니다.')
    (options, args) = parser.parse_args()
    info_file = options.info_file if len(options.info_file) > 0 \
                                  else args[0] if len(args) > 0 else ''
    if len(info_file) == 0:
        raise Exception('디바이스 설정파일을 입력하세요.')
    info_file_full_path = os.path.join(sys_config.DEVICE_INFO_PATH, info_file)
    if not os.path.exists(info_file_full_path):
        raise Exception(f'지정한 설정파일을 찾을 수 없습니다. 파일명: {info_file_full_path}')

    try:
        with open(info_file_full_path, encoding='utf-8') as dif:
            tmp_dev_info = json.load(dif)

        dev_info['host'] = tmp_dev_info['server']['host']
        dev_info['port'] = tmp_dev_info['server']['port']
        tmp_dev_not_ready = False
        try:
            tmp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tmp_socket.bind((dev_info['host'], dev_info['port']))
            tmp_dev_not_ready = True
            tmp_socket.close()
        except:
            pass
        if tmp_dev_not_ready:
            raise Exception(f'지정한 디바이스({dev_info["host"]}:{dev_info["port"]})가 '
                            f'존재하지 않습니다.')

        pdt_info_file_full_path = os.path.join(sys_config.DEVICE_INFO_PATH,
                                               f'{tmp_dev_info["device_type"]}.json')
        if not os.path.exists(pdt_info_file_full_path):
            raise Exception(f'디바이스의 제품정보 파일을 찾을 수 없습니다. '
                            f'파일명: {pdt_info_file_full_path}')

        with open(pdt_info_file_full_path, encoding='utf-8') as pif:
            tmp_pdt_info = json.load(pif)

        dev_info['co'] = tmp_pdt_info['coil']
        dev_info['di'] = tmp_pdt_info['discrete_input']
        dev_info['ir'] = tmp_pdt_info['input_register']
        dev_info['hr'] = tmp_pdt_info['holding_register']

    except Exception as e:
        raise Exception(f'설정파일을 처리하는 동안 에러가 발생했습니다.\n{str(e)}')

def help_msg():
    print('** Usage: [1:read/2:write], [count(s)/value(s)], unit-id, \n'
          ' - ex1) 1, 10, 0 => read, count=10, unit-id=0 \n'
          ' - ex2) 2, 20, 1 => write, value=20, unit-id=1 \n'
          ' - ex3) 2, [10, 20, 30], 2 => write, values=[10,20,30], unit-id=2')

def master_service():

    while True:
        send_stat = {}
        in_data = input('input data(exit=\'ctrl+c\'): ')
        if len(in_data) == 0: continue

        help_msg()




if __name__ == '__main__':

    try:
        input_parameters()
    except Exception as er:
        print(f'에러: {str(er)}')

    try:
        master_service()
    except:
        print('')
        sys.exit()