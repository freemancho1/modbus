import os
from enum import Enum, IntEnum


# log file info
USER_HOME               = os.path.expanduser('~')
FILE_PATH               = os.path.join(USER_HOME, 'projects/Data/logs/modbus/')
PREFIX_FILE_NAME        = 'modbus_slave'
FILE_NAME               = f'{PREFIX_FILE_NAME}.log'
FULL_PATH               = f'{FILE_PATH}{FILE_NAME}'

# log level info
DEFAULT_LEVEL           = 'debug'
DEFAULT_TRACE           = True
DEFAULT_DISPLAY         = True
class LEVEL(IntEnum):
    debug               = 1
    info                = 2
    warning             = 3
    error               = 4
    critical            = 5

# log size
FILE_SIZE               = '100M'    # 프로그램에서 사용할 로그파일 하나의 크기(기호는 아래 BYTE_SIZE 중 하나)
FILE_COUNT              = 10        # 프로그램에서 사용할 로그파일 갯 수
DEFAULT_FILE_SIZE       = 52428800  # 50M (size 계산에 에러가 발생할 경우 최종적으로 사용할 크기)
MAX_FILE_COUNT          = 9999      # 프로그램에서 로그 파일명으로 사용하는 일련번호 중 가장 큰 수
class BYTE_SIZE(Enum):
    B                   = 1
    K                   = 1024
    M                   = 1024 * 1024
    G                   = 1024 * 1024 * 1024
    T                   = 1024 * 1024 * 1024 * 1024

# log color
COLOR = {
    'CRITICAL': '\033[91m',
    '   ERROR': '\033[31m',
    ' WARNING': '\033[95m',
    '    INFO': '\033[93m',
    '   DEBUG': '\033[37m',
}
COLOR_END = '\033[0m'

# programming sample
IS_WRITE                = lambda x: LEVEL[x] >= LEVEL[DEFAULT_LEVEL]
# if IS_WRITE(level)