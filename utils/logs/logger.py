import re
import shutil
import traceback
from datetime import datetime

from utils.logs import config


class Logger:

    @staticmethod
    def _file_checker():
        print('Logger._file_checker')