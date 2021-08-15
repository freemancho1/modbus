import socket
import struct
from threading import Thread
from socketserver import BaseRequestHandler, ThreadingTCPServer

from utils.logs.logger import Logger
log = Logger()

class ModbusSlaveEngine:

    def __init__(self, args):
        self.args = args
        self._running = False
        self._service = None
        self._service_thread = None
        log.set_config(f'{self.args.device_type}:{self.args.host}:{self.args.port}',
                       self.args.log_level, self.args.display_log)
        log.info(f'modbus device is ready.\n{args}')
