#!/home/freeman/anaconda3/envs/modbus/bin/python
import os, sys
sys.path.append(os.path.abspath(
    os.path.join(os.path.expanduser('~'), 'projects/modbus')))

import json
import socket
from datetime import datetime
from optparse import OptionParser

import slave_config as sys_cfg


def get_config():
    cfg_file = os.path.join(sys_cfg.DEVICE_INFO_PATH,'simulator.json')
    try:
        with open(cfg_file, encoding='utf-8') as cf:
            cfg = json.load(cf)
    except Exception as er:
        raise Exception(str(er))
    return cfg


def chk_device(host, port):
    tmp_socket = None
    try:
        tmp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tmp_socket.bind((host, port))
        tmp_socket.close()
        return True
    except:
        if isinstance(tmp_socket, socket.socket):
            tmp_socket.close()
        return False


def run_device(device_config):
    print('Start device..\n')

    try:
        res_msg = []
        for key in device_config:
            dev_info = device_config[key]
            type = dev_info['type']
            host = dev_info['host']
            s_port = dev_info['port_start']
            port_cnt = dev_info['port_cnt']
            unit_cnt = dev_info['unit_cnt']
            ok_ports = []
            er_ports = []

            s_time = datetime.now()
            print(f'Running {type} device: start-port={s_port}, '
                  f'device-count={port_cnt}')
            work_cnt = 0
            while True:
                if chk_device(host, s_port):
                    ok_ports.append(s_port)
                    cmd = f'slave_device --host={host} --port={s_port} ' \
                          f'-u {unit_cnt} --device-info={type} &'
                    os.system(cmd)
                    work_cnt += 1
                else:
                    er_ports.append(s_port)
                s_port += 1
                if work_cnt > port_cnt: break
            print(f' => processing time: {datetime.now() - s_time}')

            res_msg.append(f'DEVICE: {type} - {host}\n'
                           f'  - port: {ok_ports[:1]} ~ {ok_ports[-1:]} (count: {port_cnt})\n'
                           f'  - ex-port: {er_ports}\n')

        print('\n\nRunning Result:\n')
        for msg in res_msg:
            print(msg)
    except Exception as er:
        print(f'Error: {er}')
        raise


if __name__ == '__main__':

    try:
        parser = OptionParser()
        parser.add_option('', '--init', dest='init', default=False,
                          action='store_true',
                          help='모든 포트를 종료한다.')
        (opts, args) = parser.parse_args()

        if not opts.init:
            dev_cfg = get_config()
            run_device(dev_cfg)
        else:
            kill_cmd = 'kill -9 `pgrep slave_device`'
            os.system(kill_cmd)
    except Exception as e:
        print(f'Error:\n{str(e)}')