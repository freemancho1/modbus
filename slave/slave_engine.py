import socket
import struct
from threading import Thread
from socketserver import BaseRequestHandler, ThreadingTCPServer

from slave.slave_utils import DataMgt, DataBank
from slave import slave_constants as CONST
from utils.logs.logger import Logger
log = Logger()

driver = None

class ModbusSlaveEngine:
    driver = None

    def __init__(self, args):
        self.args = args
        self._running = False
        self._service = None
        self._service_thread = None

        self._dev_info = f'{self.args.device_type}:{self.args.host}:{self.args.port}'
        log.set_config(self._dev_info, self.args.log_level, self.args.display_log)

        global driver
        driver = __import__(self.args.device_driver, fromlist=[self.args.device_driver])
        driver = driver.ModbusDriver(self.args, log)

    @property
    def _is_run(self):
        return self._running

    def _service_manager(self):
        try:
            self._running = True
            log.info('데이터 요청을 기다립니다.')
            self._service.serve_forever()
            log.info('++++++++++++++++++++++')
        except Exception as e:
            self._service.server_close()
            log.info(f'서비스 수행중 에러가 발생해 프로그램이 종료되었습니다.\n{str(e)}')
            # TODO = raise 필요성(호출한 함수에 try가 없음) 확인
            raise
        finally:
            self._running = False

    def start(self):

        if not self._is_run:
            ThreadingTCPServer.address_family = socket.AF_INET6 if self.args.ipv6 else socket.AF_INET
            ThreadingTCPServer.daemon_threads = True
            self._service = ThreadingTCPServer((self.args.host, self.args.port),
                                               self.ModbusSlaveService, bind_and_activate=False)
            self._service.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._service.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self._service.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self._service.server_bind()
            self._service.server_activate()
            log.info('정상적으로 통신 설정을 완료했습니다.')
            if self.args.no_block:
                self._service_thread = Thread(target=self._service_manager)
                self._service_thread.daemon = True
                self._service_thread.start()
            else:
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

                mbap_header = self.receve_all(CONST.MBAP_HEAD_SIZE)
                driver.chk_mbap_header(mbap_header)

                receive_body = self.receve_all(5)

                self.request.send(b'')
                break

            self.request.close()

