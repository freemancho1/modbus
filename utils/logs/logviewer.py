#!/home/freeman/anaconda3/envs/modbus/bin/python
import os
import re
import sys
import time
import threading
from optparse import OptionParser

import config as LOG_CONF
SYS_CONF = {}


class PrintLogs(threading.Thread):

    @staticmethod
    def print_log(log, pre_color):
        if SYS_CONF['log_filter'] is not None and SYS_CONF['log_filter'] not in log: return

        _opt = re.findall('\[(.*?)\]', log)
        _level = '' if len(_opt) < 2 else re.findall('\w+', _opt[0])[0].lower()
        if _level != '' and LOG_CONF.LEVEL[_level] < LOG_CONF.LEVEL[SYS_CONF['log_level_']]: return

        log_color = LOG_CONF.COLOR['   DEBUG'] if pre_color is None else pre_color
        for key in LOG_CONF.COLOR.keys():
            if key in log: log_color = LOG_CONF.COLOR[key]

        if SYS_CONF['no_time']: log = re.sub('^[\w\.\-: ]{19}\[', '[', log)
        if len(_opt) > 1:
            if SYS_CONF['no_type']: log = re.sub(f'\[{_opt[0]}\]', '', log)
            if SYS_CONF['no_pos']:
                _del_str = f'\[{_opt[1]}\]' if len(_opt) == 2 else f'\[{_opt[2]}\]'
                __del_str = ''
                for c in _del_str:
                    __del_str += '\\'+c if c in '()' else c
                log = re.sub(__del_str, '', log)
            if SYS_CONF['no_title']:
                _del_str = '' if len(_opt) == 2 else f'\[{_opt[1]}\]'
                log = re.sub(_del_str, '', log)

        print(log_color + log + LOG_CONF.COLOR_END)
        return log_color

    def run(self, *args):
        try:
            with open(SYS_CONF['log_file'], 'r') as log_file:
                if SYS_CONF['line_cnt'] == 0:
                    pre_read_lines = log_file.readlines()
                else:
                    pre_read_lines = log_file.readlines()[-SYS_CONF['line_cnt']::]
                pre_color = None
                for line in pre_read_lines:
                    pre_color = PrintLogs.print_log(line[:-1], pre_color)
                log_file.seek(log_file.tell())
                while True:
                    where = log_file.tell()
                    line = log_file.readline()
                    if not line:
                        time.sleep(.5)
                        log_file.seek(where)
                    else:
                        pre_color = PrintLogs.print_log(line[:-1], pre_color)
        except Exception as err:
            raise Exception(f'파일을 읽는 동안 에러가 발생했습니다.\n{str(err)}')


def init_parameter():
    parser = OptionParser()
    parser.add_option('-L', '--level', dest='level', default='debug',
                      help='''출력할 로그 레벨을 설정한다. 기본값은 'debug'이다.
                           debug, info, warning, error, critical을 사용할 수 있다.''')
    parser.add_option('-F', '--filter', dest='filter', default=None,
                      help='지정한 문장이 포함된 로그만 출력한다.')
    parser.add_option('-C', '--count', dest='count', default=10, type=int,
                      help='''시작시점에 출력할 라인 수를 지정한다. 기본값은 10라인이다.
                           0을 입력하면 처음부터 전체가 표시됩니다.''')
    parser.add_option('', '--no-time', dest='no_time', action='store_true',
                      default=False, help='시간정보를 출력하지 않는다.')
    parser.add_option('', '--no-type', dest='no_type', action='store_true',
                      default=False, help='로그타입 정보를 출력하지 않는다.')
    parser.add_option('', '--no-title', dest='no_title', action='store_true',
                      default=False, help='로그제목 정보를 출력하지 않는다.')
    parser.add_option('', '--no-pos', dest='no_pos', action='store_true',
                      default=False, help='로그출력 위치 정보를 출력하지 않는다.')
    (options, args) = parser.parse_args()

    log_file = LOG_CONF.FULL_PATH

    log_level = f'{options.level.upper(): >8}'
    if log_level not in LOG_CONF.COLOR.keys():
        raise Exception(f'로그 레벨은 debug, info, warning, error, critical만 사용할 수 있습니다.')

    log_filter = options.filter

    try:
        line_cnt = int(options.count) if int(options.count) >= 0 else 10
    except:
        raise Exception(f'라인수는 0 이상의 정수만 입력할 수 있습니다.')

    sys_conf = {
        'log_file'  : log_file,
        'log_level' : log_level,
        'log_level_': options.level.lower(),
        'log_filter': log_filter,
        'line_cnt'  : line_cnt,
        'no_time'   : options.no_time,
        'no_type'   : options.no_type,
        'no_title'  : options.no_title,
        'no_pos'    : options.no_pos
    }

    return sys_conf


def main():
    try:
        print_logs = PrintLogs()
        print_logs.daemon = True
        print_logs.start()

        while True:
            _ = input()
    except:
            sys.exit()


if __name__ == '__main__':

    try:
        SYS_CONF = init_parameter()
        main()
    except Exception as e:
        print(f'\n에러: {str(e)}')