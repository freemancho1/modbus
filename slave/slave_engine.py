import socket
import struct
from threading import Thread
from socketserver import BaseRequestHandler, ThreadingTCPServer

from slave.slave_utils import DataMgt, DataBank
from slave import slave_constants as CONST
from utils.logs.logger import Logger
log = Logger()

class ModbusSlaveEngine:

    def __init__(self, args):
        self.args = args
        self._running = False
        self._service = None
        self._service_thread = None
        self._dev_info = f'{self.args.device_type}:{self.args.host}:{self.args.port}'
        log.set_config(self._dev_info, self.args.log_level, self.args.display_log)

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
            # TODO - BaseRequestHandler를 ModbusService로 변경
            self._service = ThreadingTCPServer((self.args.host, self.args.port),
                                               BaseRequestHandler, bind_and_activate=False)
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
            log.info('서비스가 이미 실행중입니다.')

    def stop(self):
        if self._is_run:
            self._service.shutdown()
            self._service.server_close()
            log.info('서비스가 종료되었습니다.')


class ModbusSlaveService(BaseRequestHandler):

    def receve_all(self, size):
        if hasattr(socket, 'MSG_WAITALL'):
            data = self.request.recv(size, socket.MSG_WAITALL)
            log.debug('MSG_WAITALL 옵션을 이용한 데이터 수신')
        else:
            data = b''
            while len(data) < size:
                data += self.request.recv(size - len(data))
            log.debug('MSG_WAITALL 옵션을 사용하지 않고 데이터 수신')
        log.debug(f'요청 데이터 크기({size}), 실제 수신 데이터 크기({len(data)}) - 수신데이터: {data}')
        return data

    def handle(self):
        log.debug('요청 데이터 수신용 handler 대기중')

        while True:
            mbap_header = self.receve_all(CONST.MBAP_HEAD_SIZE)
            log.debug(f'수신된 MBAP_HEADER 데이터: {mbap_header}')
            if not (mbap_header and len(mbap_header) == CONST.MBAP_HEAD_SIZE):
                log.error(f'MBAP_HEADER 데이터 오류: 길이({len(mbap_header)}), 데이터({mbap_header})')
                break

            (transaction_id, protocol_id, data_length, unit_id) = \
                struct.unpack('>HHHB', mbap_header)
            log.debug(f'수신된 MBAP_HEADER 데이터: '
                      f'TRANSACTION ID({transaction_id}), PROTOCOL ID({protocol_id}), '
                      f'DATA LENGTH({data_length}), UNIT ID({unit_id})')
            if not ((protocol_id == 0) and (CONST.MIN_DATA_LEN < data_length < CONST.MAX_DATA_LEN)):
                log.error(f'PROTOCOL ID 데이터 또는 DATA LENGTH 데이터 오류')
                break

            receive_body = self.receve_all(data_length - 1)
            log.debug(f'수신된 데이터({len(receive_body)}): {receive_body}')
            if not (receive_body and (len(receive_body) == data_length-1)):
                log.error('수신된 데이터 또는 수신된 데이터의 길이가 요청한 데이터와 다릅니다.')
                break

            function_code = struct.unpack('B', receive_body[:1])[0]
            log.debug(f'FUNCTION CODE: 수신 데이터(receive_body[:1],{receive_body[:1]}), '
                      f'치환된 데이터({function_code})')
            if function_code > CONST.MAX_FUNC_CODE:
                log.error(f'수신된 FUNCTION CODE가 최대값인 {CONST.MAX_FUNC_CODE} 보다 큽니다.')
                break

            exp_status = CONST.EXP_NONE

            # Function code: 0x01, 0x02
            if function_code in (CONST.READ_COILS, CONST.READ_DISCRETE_INPUTS):
                (bit_address, bit_count) = struct.unpack('>HH', receive_body[1:])
                log.debug(f'FC({function_code}), SOC({receive_body[1:]}), '
                          f'bit_address({bit_address}), bit_count({bit_count})')
                if CONST.MIN_BIT_CNT <= bit_count <= CONST.MAX_BIT_CNT: # MAX 2000(0x07D0)
                    bits = DataBank.get_bits(bit_address, bit_count)
                    log.debug(f'(bit_address, bit_count) => bits({bits})')
                    if bits:
                        byte_size = round(bit_count / 8 + .5) # bit수를 8로 나누고 나머지가 있으면 1 추가
                        byte_list = [0] * byte_size
                        log.debug(f'byte size = round(bit_count/8+.5) = {byte_size}, '
                                  f'byte_list={byte_list}')
                        for i, item in enumerate(bits):
                            if item:
                                byte_pos = int(i/8)
                                byte_list[byte_pos] = DataMgt.set(byte_list[byte_pos], i%8)
                                log.debug(f'bit -> byte 치환: '
                                          f'{i}번째, byte_pos({byte_pos}), byte_list({byte_list})')
                        log.debug(f'byte_size({byte_size})와 '
                                  f'len(byte_list)({len(byte_list)}) 값 동일한가 확인!!')
                        send_body = struct.pack('BB', function_code, len(byte_list))
                        log.debug(f'send_body({send_body})='
                                  f'pack("BB", {function_code}, {len(byte_list)})')
                        for byte in byte_list:
                            send_body += struct.pack('B', byte)
                        log.debug(f'send_body+pack(byte_list): {send_body}, byte_list: {byte_list}')
                    else:
                        exp_status = CONST.EXP_DATA_ADDRESS
                        log.error(f'{CONST.EXP_DETAILS[exp_status]}, '
                                  f'address({bit_address}), bits({bits})')
                else:
                    exp_status = CONST.EXP_DATA_VALUE
                    log.error(f'{CONST.EXP_DETAILS[exp_status]}, bit_count({bit_count})')

            # Function code: 0x03, 0x04
            if function_code in (CONST.READ_HOLDING_REGISTERS, CONST.READ_INPUT_REGISTERS):
                (word_address, word_count) = struct.unpack('>HH', receive_body[1:])
                log.debug(f'FC({function_code}), SOC({receive_body[1:]}), '
                          f'word_address({word_address}), word_count({word_count})')
                if CONST.MIN_WORD_CNT <= word_count <= CONST.MAX_WORD_CNT: # MAX 125(0x7D)
                    words = DataBank.get_words(word_address, word_count)