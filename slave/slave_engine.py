import socket
import struct
from threading import Thread
from socketserver import BaseRequestHandler, ThreadingTCPServer

from slave.slave_utils import DataMgt, DataBank
from slave import slave_constants as CONST
from utils.logs.logger import Logger
log = Logger()

unitDataBank = [DataBank() for _ in range(CONST.MAX_UNIT_CNT)]

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
            self._service = ThreadingTCPServer((self.args.host, self.args.port),
                                               ModbusSlaveService, bind_and_activate=False)
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
            if not (mbap_header and len(mbap_header) == CONST.MBAP_HEAD_SIZE):
                if mbap_header != b'':  # connect(), close() 함수만 실행하면 b''값이 넘어옴
                    log.error(f'MBAP_HEADER 데이터 오류: 길이({len(mbap_header)}), 데이터({mbap_header})')
                break

            (transaction_id, protocol_id, data_length, unit_id) = \
                struct.unpack('>HHHB', mbap_header)
            log.debug(f'mbap_header: tran_id={transaction_id}, prot_id={protocol_id}, '
                      f'data_len={data_length}, unit_id={unit_id}')
            if not ((protocol_id == 0) and (CONST.MIN_DATA_LEN < data_length < CONST.MAX_DATA_LEN)):
                log.error(f'PROTOCOL ID 데이터 또는 DATA LENGTH 데이터 오류')
                break
            if unit_id >= CONST.MAX_UNIT_CNT:
                log.error(f'지정한 UNIT 수를 초과했습니다. '
                          f'최대 UNIT수={CONST.MAX_UNIT_CNT}, 요청 UNIT_ID={unit_id}')
                break

            receive_body = self.receve_all(data_length - 1)
            if not (receive_body and (len(receive_body) == data_length-1)):
                log.error('수신된 데이터 또는 수신된 데이터의 길이가 요청한 데이터와 다릅니다.')
                break

            function_code = struct.unpack('B', receive_body[:1])[0]
            if function_code > CONST.MAX_FUNC_CODE:
                log.error(f'수신된 FUNCTION CODE{function_code}가 '
                          f'최대값인 {CONST.MAX_FUNC_CODE} 보다 큽니다.')
                break

            exp_status = CONST.EXP_NONE

            # Function code: 0x01, 0x02
            if function_code in (CONST.READ_COILS, CONST.READ_DISCRETE_INPUTS):
                (bit_address, bit_count) = struct.unpack('>HH', receive_body[1:])
                log.debug(f'fc={function_code}, address={bit_address}, count={bit_count}')
                if CONST.MIN_BIT_CNT <= bit_count <= CONST.MAX_BIT_CNT: # MAX 2000(0x07D0)
                    bits = unitDataBank[unit_id].get_bits(bit_address, bit_count)
                    _msg = 'return value'
                    _msg = _msg if bit_count==1 else f'{_msg}s'
                    log.info(f'{_msg}={bits}')
                    if bits:
                        byte_size = round(bit_count / 8 + .5) # bit수를 8로 나누고 나머지가 있으면 1 추가
                        byte_list = [0] * byte_size
                        for i, item in enumerate(bits):
                            if item:
                                byte_pos = int(i/8)
                                byte_list[byte_pos] = DataMgt.set_bit(byte_list[byte_pos], i%8)
                        send_body = struct.pack('BB', function_code, len(byte_list))
                        for byte in byte_list:
                            send_body += struct.pack('B', byte)
                        log.debug('send_body="BBB...", fc, len(byte_list), byte...')
                        log.info(f'send_body={send_body}')
                    else:
                        exp_status = CONST.EXP_DATA_ADDRESS
                        log.error(f'{CONST.EXP_DETAILS[exp_status]}, '
                                  f'address={bit_address}, get_bits={bits}')
                else:
                    exp_status = CONST.EXP_DATA_VALUE
                    log.error(f'{CONST.EXP_DETAILS[exp_status]}, bit_count={bit_count}')

            # Function code: 0x03, 0x04
            elif function_code in (CONST.READ_HOLDING_REGISTERS, CONST.READ_INPUT_REGISTERS):
                (word_address, word_count) = struct.unpack('>HH', receive_body[1:])
                log.debug(f'fc={function_code}, address={word_address}, count={word_count}')
                if CONST.MIN_WORD_CNT <= word_count <= CONST.MAX_WORD_CNT: # MAX 125(0x7D)
                    words = unitDataBank[unit_id].get_words(word_address, word_count)
                    log.info(f'return values={words}')
                    if words:
                        send_body = struct.pack('BB', function_code, word_count*2)
                        for word in words:
                            send_body += struct.pack('>H', word)
                        log.debug('send_body="BBH...", fc, count*2, word...')
                        log.info(f'send_body={send_body}')
                    else:
                        exp_status = CONST.EXP_DATA_ADDRESS
                        log.error(f'{CONST.EXP_DETAILS[exp_status]}, address={word_address}')
                else:
                    exp_status = CONST.EXP_DATA_VALUE
                    log.error(f'{CONST.EXP_DETAILS[exp_status]}, count={word_count}')

            # Function code: 0x05
            elif function_code is CONST.WRITE_SINGLE_COIL:
                (bit_address, bit_value) = struct.unpack('>HH', receive_body[1:])
                _bit_value = bool(bit_value == 0xFF00)
                log.debug(f'fc={function_code}, address={bit_address}, value={bit_value}')
                if unitDataBank[unit_id].set_bits(bit_address, [_bit_value]):
                    log.info(f'write value={_bit_value}')
                    send_body = struct.pack('>BHH', function_code, bit_address, bit_value)
                    log.debug(f'send_body=">BHH", fc, addr, value(convert value)')
                    log.info(f'send_body={send_body}({_bit_value})')
                else:
                    exp_status = CONST.EXP_DATA_ADDRESS
                    log.error(f'{CONST.EXP_DETAILS[exp_status]}, '
                              f'address={bit_address}, value={bit_value}')

            # Function code: 0x06
            elif function_code is CONST.WRITE_SINGLE_REGISTER:
                (word_address, word_value) = struct.unpack('>HH', receive_body[1:])
                log.debug(f'fc={function_code}, address={word_address}, value={word_value}')
                if unitDataBank[unit_id].set_words(word_address, [word_value]):
                    log.info(f'write value={word_value}')
                    send_body = struct.pack('>BHH', function_code, word_address, word_value)
                    log.debug('send_body=">BHH", fc, addr, value')
                    log.info(f'send_body={send_body}')
                else:
                    exp_status = CONST.EXP_DATA_ADDRESS
                    log.error(f'{CONST.EXP_DETAILS[exp_status]}, '
                              f'address={word_address}, value={word_value}')

            # Function code: 0x0F
            elif function_code is CONST.WRITE_MULTIPLE_COILS:
                (bit_address, bit_count, byte_count) = struct.unpack('>HHB', receive_body[1:6])
                log.debug(f'fc={function_code}, address={bit_address}, '
                          f'count={bit_count}, byte_count={byte_count}')
                if (CONST.MIN_BIT_CNT <= bit_count <= CONST.MAX_BIT_0F_CNT) and \
                    (byte_count >= (bit_count/8)):
                    bits = [False] * bit_count
                    for i, item in enumerate(bits):
                        bit_pos = int(i/8) + 6
                        bit_value = struct.unpack('B', receive_body[bit_pos:bit_pos+1])[0]
                        bits[i] = DataMgt.test_bit(bit_value, i % 8)
                    log.info(f'write value={bits}')
                    if unitDataBank[unit_id].set_bits(bit_address, bits):
                        send_body = struct.pack('>BHH', function_code, bit_address, bit_count)
                        log.debug('send_body=">BHH", fc, address, count')
                        log.info(f'send_body={send_body}')
                    else:
                        exp_status = CONST.EXP_DATA_ADDRESS
                        log.error(f'{CONST.EXP_DETAILS[exp_status]}, '
                                  f'address={bit_address}, values={bits}')
                else:
                    exp_status = CONST.EXP_DATA_VALUE
                    log.error(f'{CONST.EXP_DETAILS[exp_status]}, '
                              f'bit count={bit_count}, byte count={byte_count}')

            # Function code: 0x10
            elif function_code is CONST.WRITE_MULTIPLE_REGISTERS:
                (word_address, word_count, byte_count) = struct.unpack('>HHB', receive_body[1:6])
                log.debug(f'fc={function_code}, address={word_address}, '
                          f'count={word_count}, byte_count={byte_count}')
                if (CONST.MIN_WORD_CNT <= word_count <= CONST.MAX_WORD_10_CNT) and \
                    (byte_count == word_count * 2):
                    word_list = [0] * word_count
                    for i, item in enumerate(word_list):
                        word_offset = i * 2 + 6
                        word_list[i] = struct.unpack('>H', receive_body[word_offset:word_offset+2])[0]
                    log.info(f'write values={word_list}')
                    if unitDataBank[unit_id].set_words(word_address, word_list):
                        send_body = struct.pack('>BHH', function_code, word_address, word_count)
                        log.debug('send_body=">BHH", fc, address, count')
                        log.info(f'send_body={send_body}')
                    else:
                        exp_status = CONST.EXP_DATA_ADDRESS
                        log.error(f'{CONST.EXP_DETAILS[exp_status]}, '
                                  f'address={word_address}, count={word_count}')
                else:
                    exp_status = CONST.EXP_DATA_VALUE
                    log.error(f'{CONST.EXP_DETAILS[exp_status]}, '
                              f'word count={word_count}, byte count={byte_count}')

            # 기능코드 에러 처리
            else:
                exp_status = CONST.EXP_ILLEGAL_FUNCTION
                log.error(f'{CONST.EXP_DETAILS[exp_status]}, fc={function_code}')

            # 디바이스 에러 처리(ADDRESS, VALUE)
            if exp_status != CONST.EXP_NONE:
                send_body = struct.pack('BB', function_code+0x80, exp_status)
                log.debug('error send_body="BB", fc+0x80, exp_status')
                log.error(f'error send_body={send_body}')

            send_header = struct.pack('>HHHB', transaction_id, protocol_id, len(send_body)+1, unit_id)
            log.debug(f'send_head: "HHHB", tran_id, prot_id, len(send_body)+1, unit_id')
            log.info(f'send_head={send_header}')
            self.request.send(send_header+send_body)

        self.request.close()
