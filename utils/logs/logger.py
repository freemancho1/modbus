import os
import re
import shutil
import traceback
from datetime import datetime

from utils.logs import config as LOG_CONF


class Logger:

    def __init__(self):
        self._name = None
        self._level = LOG_CONF.DEFAULT_LEVEL
        self._display = LOG_CONF.DEFAULT_DISPLAY
        self._tracing = LOG_CONF.DEFAULT_TRACE

    def set_config(self, name=None,
                   level=LOG_CONF.DEFAULT_LEVEL,
                   display=LOG_CONF.DEFAULT_DISPLAY,
                   tracing=LOG_CONF.DEFAULT_TRACE):
        self._name = name
        self.set_level(level)
        self.set_display(display)
        self.set_trace(tracing)

    def __str__(self):
        return f'Log(name={self._name}, level={self._level}, ' \
               f'display={self._display}, tracing={self._tracing})'

    def set_level(self, level=LOG_CONF.DEFAULT_LEVEL):
        _level = level.lower()
        self._level = _level if hasattr(LOG_CONF.LEVEL, _level) \
                             else LOG_CONF.DEFAULT_LEVEL

    def set_display(self, display):
        self._display = True if display else False

    def set_trace(self, tracing):
        self._tracing = True if tracing else False

    def _is_write(self, level):
        return LOG_CONF.LEVEL[level] >= LOG_CONF.LEVEL[self._level]

    @property
    def _is_display(self):
        return self._display

    @property
    def _is_trace(self):
        return self._tracing

    def _log_writer(self, level, message):

        def log_file_manager():

            def log_file_create():
                new_log_file = open(LOG_CONF.FULL_PATH, 'w')
                new_log_file.close()

            def log_file_move():
                curr_log_file_cnt = 0
                max_log_file_cnt = min(LOG_CONF.MAX_FILE_COUNT, LOG_CONF.FILE_COUNT)
                min_ctime, max_ctime = float('inf'), float('-inf')
                min_file_name, max_file_name = '', ''
                for file_name in os.listdir(LOG_CONF.FILE_PATH):
                    if re.findall(LOG_CONF.PREFIX_FILE_NAME+'\-\d{5}\.log', file_name):
                        curr_log_file_cnt += 1
                        curr_ctime = os.path.getctime(os.path.join(LOG_CONF.FILE_PATH, file_name))
                        if min_ctime > curr_ctime:  # 삭제할 파일을 찾기 위해 가장 오래된 파일 선택
                            min_ctime, min_file_name = curr_ctime, file_name
                        if max_ctime < curr_ctime:  # 신규파일 생성 일련번호를 찾기위해 가장 최신 파일 선택
                            max_ctime, max_file_name = curr_ctime, file_name
                if curr_log_file_cnt >= max_log_file_cnt:
                    os.remove(os.path.join(LOG_CONF.FILE_PATH, min_file_name))
                if curr_log_file_cnt == 0:
                    new_file_number = 0
                else:
                    new_file_number = int(re.findall('\d{5}', max_file_name)[0])
                    if new_file_number > LOG_CONF.MAX_FILE_COUNT:
                        new_file_number = 0
                    else:
                        new_file_number += 1
                new_log_file_name = f'{LOG_CONF.PREFIX_FILE_NAME}-{new_file_number:05d}.log'
                shutil.move(LOG_CONF.FULL_PATH, os.path.join(LOG_CONF.FILE_PATH, new_log_file_name))
                log_file_create()

            if not os.path.exists(LOG_CONF.FILE_PATH):
                os.makedirs(LOG_CONF.FILE_PATH, exist_ok=True)

            try:
                curr_log_size = os.path.getsize(LOG_CONF.FULL_PATH)
            except:
                log_file_create()
                curr_log_size = 0

            try:
                max_log_size = LOG_CONF.BYTE_SIZE[LOG_CONF.FILE_SIZE[-1:]].value * \
                               int(LOG_CONF.FILE_SIZE[:-1])
            except:
                max_log_size = LOG_CONF.DEFAULT_FILE_SIZE

            if curr_log_size > max_log_size: log_file_move()

        if self._is_write(level):

            log_message = '' if self._name is None else f'[{self._name}]'
            if self._is_trace:
                trace = re.findall('.*?"([\w_\-]+).*line (\d*), in (.*)', traceback.format_stack()[-3])
                try:
                    log_message += f'[{trace[0][0]}({trace[0][1]}).{trace[0][2]}]'
                except:
                    trace = re.findall('.*/([\w_\-]+).*line (\d*), in (.*)', traceback.format_stack()[-3])
                    try:
                        log_message += f'[{trace[0][0]}({trace[0][1]}).{trace[0][2]}]'
                    except:
                        pass
            log_message = f'{datetime.now():%Y-%m-%d %H:%M:%S}[{level.upper():>8}]' \
                          f'{log_message} {message}'

            if self._is_display: print(log_message)

            log_file_manager()
            with open(LOG_CONF.FULL_PATH, 'a') as log_file:
                log_file.write(f'{log_message}\n')

    def debug(self, msg):
        self._log_writer('debug', msg)

    def info(self, msg):
        self._log_writer('info', msg)

    def warning(self, msg):
        self._log_writer('warning', msg)

    def error(self, msg):
        self._log_writer('error', msg)

    def critical(self, msg):
        self._log_writer('critical', msg)
