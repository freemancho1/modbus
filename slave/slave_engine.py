import socket
from datetime import datetime
from threading import Thread
from socketserver import BaseRequestHandler, ThreadingTCPServer

from slave import slave_constants as CONST
from utils import sys_config as SYS_CONF
from utils.logs.logger import Logger
log = Logger()

driver = None

class ModbusSlaveEngine:

    def __init__(self, args):
        self.device_info = args.device_info
        self.product_info = args.product_info
        self.log_level = args.log_level
        # self.display_log = args.display_log
        self.display_log = False
        self._running = False
        self._service = None
        self._service_thread = None

        self._dev_info = f'{self.device_info["type"]}:' \
                         f'{self.device_info["host"]}:{self.device_info["port"]}'
        log.set_config(self._dev_info, self.log_level, self.display_log)

        global driver
        driver_name = f'{SYS_CONF.DRIVER_PATH.replace("/", ".")}.{self.product_info["driver"]}'
        driver = __import__(driver_name, fromlist=[driver_name])
        driver = driver.ModbusDriver(self.device_info, self.product_info, log)

    @property
    def _is_run(self):
        return self._running

    def _service_manager(self):
        try:
            self._running = True
            log.info('데이터 요청을 기다립니다.')
            self._service.serve_forever()
        except Exception as e:
            self._service.server_close()
            log.info(f'서비스 수행중 에러가 발생해 프로그램이 종료되었습니다.\n{str(e)}')
        finally:
            self._running = False

    def start(self):

        if not self._is_run:
            ThreadingTCPServer.address_family = socket.AF_INET
            ThreadingTCPServer.daemon_threads = True
            self._service = ThreadingTCPServer((self.device_info['host'], self.device_info['port']),
                                               ModbusSlaveService, bind_and_activate=False)
            self._service.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._service.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self._service.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self._service.server_bind()
            self._service.server_activate()
            log.info('정상적으로 통신 설정을 완료했습니다.')
            self._service_manager()
        else:
            log.warning('서비스가 이미 실행중입니다.')

    def stop(self):
        if self._is_run:
            self._service.shutdown()
            self._service.server_close()
            log.info('서비스가 종료되었습니다.')


class ModbusSlaveService(BaseRequestHandler):

    def receve_all(self, size):
        if hasattr(socket, 'MSG_WAITALL'):
            data = self.request.recv(size, socket.MSG_WAITALL)
        else:
            data = b''
            while len(data) < size:
                data += self.request.recv(size - len(data))
        log.info(f'recv_data={data}')
        return data

    def handle(self):

        while True:
            driver.init_transaction()

            mbap_header = self.receve_all(CONST.MBAP_HEAD_SIZE)
            s_time = datetime.now()
            data_len = driver.chk_mbap_header(mbap_header)
            if data_len < CONST.MIN_DATA_LEN: break

            receive_body = self.receve_all(data_len-1)
            if not driver.chk_receive_body(receive_body): break

            self.request.send(driver.modbus_processing())
            log.warning(f'processing time: {datetime.now()-s_time}')

        self.request.close()

