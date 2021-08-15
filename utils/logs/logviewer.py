import os
import sys
import time
import threading
from optparse import OptionParser

import config as LOG_CONF


LOG_FILE = None
LOG_LEVEL = 'debug'
LOG_FILTER = None
LINE_CNT = 10


class PrintLogs(threading.Thread):

    @staticmethod
    def print_log(log):
        if LOG_FILTER is not None and LOG_FILTER not in log: return
        log_color = LOG_CONF.COLOR['   DEBUG']
        for key in LOG_CONF.COLOR.keys():
            if key in log: log_color = LOG_CONF.COLOR[key]
        print(log_color + log + LOG_CONF.COLOR_END)

    def run(self, *args):
        try:
            with open(LOG_FILE, 'r') as log_file:
                if LINE_CNT == 0:
                    pre_read_lines = log_file.readlines()
                else:
                    pre_read_lines = log_file.readlines()[-LINE_CNT::]
                for line in pre_read_lines:
                    PrintLogs.print_log(line[:-1])
                log_file.seek(log_file.tell())
                while True:
                    where = log_file.tell()
                    line = log_file.readline()
                    if not line:
                        time.sleep(.5)
                        log_file.seek(where)
                    else:
                        PrintLogs.print_log(line[:-1])
        except Exception as err:
            raise Exception(f'파일을 읽는 동안 에러가 발생했습니다.\n{str(err)}')


def init_parameter():
    parser = OptionParser()
    parser.add_option('-L', '--level', dest='level', default='debug',
                      help='''출력할 로그 레벨을 설정한다. 기본값은 'debug'이다.
                           debug, info, warning, error, critical을 사용할 수 있다.''')
    parser.add_option('-F', '--filter', dest='filter', default=None,
                      help='지정한 문장이 포함된 로그만 출력한다.')
    parser.add_option('-C', '--count', dest='count', default=10,
                      help='''시작시점에 출력할 라인 수를 지정한다. 기본값은 10라인이다.
                           0을 입력하면 처음부터 전체가 표시됩니다.''')
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

    return log_file, log_level, log_filter, line_cnt


def main():
    print_logs = PrintLogs()
    print_logs.daemon = True
    print_logs.start()

    while True:
        try:
            _ = input()
        except:
            sys.exit()



if __name__ == '__main__':

    try:
        LOG_FILE, LOG_LEVEL, LOG_FILTER, LINE_CNT = init_parameter()
        main()
    except Exception as e:
        print(f'\n에러: {str(e)}')