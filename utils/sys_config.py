import os


USER_HOME               = os.path.expanduser('~')
PROJECT_NAME            = 'modbus'
PROJECT_HOME            = os.path.join(USER_HOME, 'projects', PROJECT_NAME)

DEVICE_INFO_PATH        = os.path.join(PROJECT_HOME, 'device_info')
DRIVER_PATH             = 'drivers'     # dev_info/drivers 등 폴더를 이용해도 됨
DRIVER_FULL_PATH        = os.path.join(PROJECT_HOME, DRIVER_PATH)


# 최대 UNIT 갯수
MAX_UNIT_CNT            = 10