#!/home/freeman/anaconda3/envs/modbus/bin/python
import os
import re
import sys
import json
import socket
sys.path.append(os.path.abspath(
    os.path.join(os.path.expanduser('~'), 'projects/modbus')))

from datetime import datetime
from optparse import OptionParser
from pymodbus.client.sync import ModbusTcpClient

from slave import slave_config

dev_info = {}


def input_parameters():

    parser = OptionParser()
    parser.add_option('-H', '--host', dest='host', default='127.0.0.1',
                      help='디바이스(들) IP정보, 기본값 127.0.0.1')
    (options, args) = parser.parse_args()

    dev_info['host'] = options.host
    dev_info['addr'] = [
        [0, 9999], [10000, 19999], [40000, 49999], [30000, 39999]]


def help_msg():
    print('** Usage: port, [1:read/2:write], address, [count/value(s)], unit-id, \n'
          ' - ex1) 5021, 1, 100, 10, 0              => 5021, read, address=100, count=10, unit-id=0 \n'
          ' - ex2) 5021, 2, 40011, 20, 1            => 5021, write, address=40011, value=20, unit-id=1 \n'
          ' - ex3) 5021, 2, 40100, [10, 20, 30], 2  => 5021, write, address=40100, values=[10,20,30], unit-id=2 \n'
          ' - ex4) 5021, 2, 15, [True]*3            => 5021, write, address=15, values=[True, True, True], unit-id=0 \n\n'
          '** Usage: [clear/help]\n')

def chk_service():
    pass

def master_service():

    while True:
        send_stat = {}

        in_data = input('Exit=\'Ctrl+C\', Help=\'H\'] Input Data: ')

        if len(in_data) == 0: continue
        if not in_data[0].isdigit():
            if in_data == 'clear':
                cmd = 'cls' if os.name in ('nt', 'dos') else 'clear'
                os.system(cmd)
            else:
                help_msg()
            continue

        in_data = in_data.replace('True', '1').replace('False', '0')

        send_stat['type'] = int(in_data[:1])

        try:
            if '[' in in_data and ']' in in_data:
                tmp_val = re.findall('\[([\w\,\d ]+)\]', in_data)[0]
                tmp_lst = [int(i) for i in tmp_val.split(',')]
                tmp_cnt = re.findall('\] *\* *([\d]+)', in_data)
                count = int(tmp_cnt[0]) if len(tmp_cnt) > 0 else 1
                send_stat['value'] = tmp_lst * count
                in_data = in_data.replace(f'[{tmp_val}]','')
                tmp_val = in_data.split(',')
            elif '[' in in_data or ']' in in_data:
                raise Exception('대괄호가 한쪽이 없습니다.')
            else:
                tmp_val = in_data.split(',')
                send_stat['value'] = int(tmp_val[3])

            if len(tmp_val) > 5:
                raise Exception('입력 데이터의 갯 수가 초과되었습니다.')

            send_stat['port'] = int(tmp_val[0])
            send_stat['type'] = int(tmp_val[1])
            send_stat['addr'] = int(tmp_val[2])
            send_stat['uid'] = int(tmp_val[4]) if len(tmp_val) == 5 else 0
        except Exception as e:
            print(f'Input data error. data: {in_data} => {e}')
            continue

        try:
            tmp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tmp_socket.bind((dev_info['host'], send_stat['port']))
            tmp_socket.close()
            print(f'Input service port is not ready. port={send_stat["port"]}')
            continue
        except:
            pass

        client = ModbusTcpClient(dev_info['host'], send_stat['port'])
        call_func = [
            [client.read_coils, client.read_discrete_inputs,
             client.read_holding_registers, client.read_input_registers],
            [client.write_coil, client.write_register,
             client.write_coils, client.write_registers]
        ]

        reg_type = [i for i in range(len(dev_info['addr']))
                    if dev_info['addr'][i][0] <= send_stat['addr'] <= dev_info['addr'][i][1]]
        if len(reg_type) == 0:
            print(f'Input address error. address: {send_stat["addr"]}')
            continue
        else:
            reg_type = reg_type[0]

        if send_stat['type'] == 2:
            if reg_type < 2:
                _reg_type = 0 if isinstance(send_stat['value'], int) else 2
            else:
                _reg_type = 1 if isinstance(send_stat['value'], int) else 3
            reg_type = _reg_type

        s = datetime.now()

        try:
            if send_stat['type'] == 1:
                r = call_func[0][reg_type](address=send_stat['addr'],
                                           count=send_stat['value'],
                                           unit=send_stat['uid'])
                print(f'{r.bits[:send_stat["value"]] if reg_type < 2 else r.registers} '
                      f'=> processing time: {datetime.now()-s}')
            else:
                if reg_type < 2:
                    r = call_func[1][reg_type](address=send_stat['addr'],
                                               value=send_stat['value'],
                                               unit=send_stat['uid'])
                else:
                    r = call_func[1][reg_type](address=send_stat['addr'],
                                               values=send_stat['value'],
                                               unit=send_stat['uid'])

                print(f'{r} => processing time: {datetime.now()-s}')
        except:
            print(f'Input data error. data={send_stat}')
        print()

        client.close()



if __name__ == '__main__':

    try:
        input_parameters()
    except Exception as er:
        print(f'에러: {str(er)}')
        sys.exit()

    try:
        master_service()
    except:
        print('')   # ctrl+c 클릭시 개행 위해 사용
        sys.exit()