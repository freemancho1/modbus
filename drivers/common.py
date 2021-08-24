import os
import time
import struct
import threading
from datetime import datetime, timedelta
from random import randint, random

from slave import slave_constants as CONST
from slave.slave_utils import DataMgt, DataBank

class CommonDriver:

    def __init__(self, device_info, product_info, log):
        self.device_info = device_info
        self.product_info = product_info
        self.log = log
        self.const = CONST

        self.co = self.product_info['coil'].get('data',[])
        self.di = self.product_info['discrete_input'].get('data',[])
        self.ir = self.product_info['input_register'].get('data',[])
        self.hr = self.product_info['holding_register'].get('data',[])

        self.DataBank = [DataBank() for _ in range(self.device_info['unit_count'])]
        self.ws_addr = self.product_info['input_register']['start_addr']  # register start address

        self.timer = {}
        self._sys_data = {}

        self.tid, self.pid, self.len, self.uid = 0, 0, 0, 0
        self.fc = 0
        self.address = 0        # 수신받은 address
        self._address = 0       # 메모리상 address
        self.count = 0
        self.byte_count = 0
        self.value = 0
        self.exp_status = CONST.EXP_NONE
        self.recv_body = b''
        self.send_body = b''

        self._init_device()

        # self.product_info['generation_interval'] = 100
        gd_process = GenerationData(self.device_generation_data,
                                    self.product_info['generation_interval'])
        gd_process.daemon = True
        gd_process.start()

    def init_transaction(self):
        self.tid, self.pid, self.len, self.uid = 0, 0, 0, 0
        self.fc, self.address, self._address = 0, 0, 0
        self.count, self.byte_count, self.value = 0, 0, 0
        self.exp_status = CONST.EXP_NONE
        self.recv_body = b''
        self.send_body = b''

    def chk_mbap_header(self, mbap_header):

        if not (mbap_header and len(mbap_header) == CONST.MBAP_HEAD_SIZE):
            if mbap_header != b'':  # connect(), close() 함수만 실행하면 b''값이 넘어옴
                self.log.error(f'MBAP_HEADER 데이터 오류: 길이({len(mbap_header)}), 데이터({mbap_header})')
            return 0

        (self.tid, self.pid, self.len, self.uid) = struct.unpack('>HHHB', mbap_header)
        self.log.debug(f'mbap_header: transaction_id={self.tid}, protocol_id={self.pid}, '
                       f'data_length={self.len}, unit_id={self.uid}')

        if not ((self.pid == 0) and (CONST.MIN_DATA_LEN < self.len < CONST.MAX_DATA_LEN)):
            self.log.error(f'PROTOCOL ID 데이터 또는 DATA LENGTH 데이터 오류')
            return 0

        if self.uid >= self.device_info['unit_count']:
            self.log.error(f'지정한 UNIT 수를 초과했습니다. '
                           f'최대 UNIT수={CONST.MAX_UNIT_CNT}, 요청 UNIT_ID={self.uid}')
            return 0

        return self.len

    def chk_receive_body(self, receive_body):

        if not (receive_body and (len(receive_body) == self.len - 1)):
            self.log.error('수신된 데이터 또는 수신된 데이터의 길이가 요청한 데이터와 다릅니다.')
            return False

        self.fc = struct.unpack('B', receive_body[:1])[0]
        self.recv_body = receive_body
        if self.fc > CONST.MAX_FUNC_CODE:
            self.log.error(f'수신된 FUNCTION CODE{self.fc}가 '
                           f'최대값인 {CONST.MAX_FUNC_CODE} 보다 큽니다.')
            return False

        return True

    def _chk_address(self):
        self.address = struct.unpack('>H', self.recv_body[1:3])[0]
        m_addr = [[self.product_info['coil']['start_addr'],
                   self.product_info['coil']['end_addr']],
                  [self.product_info['discrete_input']['start_addr'],
                   self.product_info['discrete_input']['end_addr']],
                  [self.product_info['input_register']['start_addr'],
                   self.product_info['input_register']['end_addr']],
                  [self.product_info['holding_register']['start_addr'],
                   self.product_info['holding_register']['end_addr']]]

        if self.fc in (CONST.READ_COILS, CONST.WRITE_MULTIPLE_COILS, CONST.WRITE_SINGLE_COIL):
            if m_addr[0][0] <= self.address < m_addr[0][1] - CONST.MAX_BIT_CNT:
                self._address = self.address
            else:
                self.exp_status = CONST.EXP_DATA_ADDRESS
                self.log.error(f'{CONST.EXP_DETAILS[self.exp_status]}, '
                               f'function code={self.fc}, address={self.address}')
                return False
        elif self.fc is CONST.READ_DISCRETE_INPUTS:
            if m_addr[1][0] <= self.address < m_addr[1][1] - CONST.MAX_BIT_CNT:
                self._address = self.address
            else:
                self.exp_status = CONST.EXP_DATA_ADDRESS
                self.log.error(f'{CONST.EXP_DETAILS[self.exp_status]}, '
                               f'function code={self.fc}, address={self.address}')
                return False
        elif self.fc is CONST.READ_INPUT_REGISTERS:
            if m_addr[2][0] <= self.address < m_addr[2][1] - CONST.MIN_WORD_CNT:
                self._address = self.address - self.ws_addr
            else:
                self.exp_status = CONST.EXP_DATA_ADDRESS
                self.log.error(f'{CONST.EXP_DETAILS[self.exp_status]}, '
                               f'function code={self.fc}, address={self.address}')
                return False
        else:
            if m_addr[3][0] <= self.address < m_addr[3][1] - CONST.MIN_WORD_CNT:
                self._address = self.address - self.ws_addr
            else:
                self.exp_status = CONST.EXP_DATA_ADDRESS
                self.log.error(f'{CONST.EXP_DETAILS[self.exp_status]}, '
                               f'function code={self.fc}, address={self.address}')
                return False
        return True

    def _chk_recv_etc(self):
        if self.fc <= CONST.READ_INPUT_REGISTERS:
            self.count = struct.unpack('>H', self.recv_body[3:])[0]
            self.log.debug(f'fc={self.fc}, address={self.address}, count={self.count}')
            if self.fc in (CONST.READ_COILS, CONST.READ_DISCRETE_INPUTS):
                _min_value, _max_value = CONST.MIN_BIT_CNT, CONST.MAX_BIT_CNT
            else:
                _min_value, _max_value = CONST.MIN_WORD_CNT, CONST.MAX_WORD_CNT
            if not (_min_value <= self.count <= _max_value):
                self.exp_status = CONST.EXP_DATA_VALUE
                self.log.error(f'{CONST.EXP_DETAILS[self.exp_status]}, count={self.count}')
                return False
        elif self.fc in (CONST.WRITE_SINGLE_COIL, CONST.WRITE_SINGLE_REGISTER):
            self.value = struct.unpack('>H', self.recv_body[3:])[0]
            self.log.debug(f'fc={self.fc}, address={self.address}, value={self.value}')
        else:
            (self.count, self.byte_count) = struct.unpack('>HB', self.recv_body[3:6])
            self.log.debug(f'fc={self.fc}, address={self.address}, '
                           f'count={self.count}, byte_count={self.byte_count}')
            if self.fc is CONST.WRITE_MULTIPLE_COILS:
                _min_value, _max_value, _chk_value = \
                    CONST.MIN_BIT_CNT, CONST.MAX_BIT_0F_CNT, self.count / 8
                self.value = [False] * self.count
                for i, item in enumerate(self.value):
                    bit_pos = int(i / 8) + 6
                    bit_value = struct.unpack('B', self.recv_body[bit_pos:bit_pos + 1])[0]
                    self.value[i] = DataMgt.test_bit(bit_value, i % 8)
                self.log.debug(f'write value={self.value}')
            else:
                _min_value, _max_value, _chk_value = \
                    CONST.MIN_WORD_CNT, CONST.MAX_WORD_10_CNT, self.count * 2
                self.value = [0] * self.count
                for i, item in enumerate(self.value):
                    word_offset = i * 2 + 6
                    self.value[i] = struct.unpack('>H', self.recv_body[word_offset:word_offset + 2])[0]
                self.log.debug(f'write values={self.value}')
            if not (_min_value <= self.count <= _max_value and self.byte_count >= _chk_value):
                self.exp_status = CONST.EXP_DATA_VALUE
                self.log.error(f'{CONST.EXP_DETAILS[self.exp_status]}, count={self.count}')
                return False
        return True

    def _read_bits(self):
        bits = self.DataBank[self.uid].get_bits(self.address, self.count)
        _msg = 'return value'
        _msg = _msg if self.count == 1 else f'{_msg}s'
        self.log.debug(f'{_msg}={bits}')
        if bits:
            byte_size = round(self.count / 8 + .5)  # bit수를 8로 나누고 나머지가 있으면 1 추가
            byte_list = [0] * byte_size
            for i, item in enumerate(bits):
                if item:
                    byte_pos = int(i / 8)
                    byte_list[byte_pos] = DataMgt.set_bit(byte_list[byte_pos], i % 8)
            self.send_body = struct.pack('BB', self.fc, len(byte_list))
            for byte in byte_list:
                self.send_body += struct.pack('B', byte)
            self.log.debug('send_body="BBB...", fc, len(byte_list), byte...')
            self.log.info(f'send_body={self.send_body}')
        else:
            self.exp_status = CONST.EXP_DATA_ADDRESS
            self.log.error(f'{CONST.EXP_DETAILS[self.exp_status]}, '
                           f'address={self.address}, get_bits={bits}')

    def _read_registers(self):
        words = self.DataBank[self.uid].get_words(self._address, self.count)
        self.log.debug(f'return values={words}')
        if words:
            self.send_body = struct.pack('BB', self.fc, self.count * 2)
            for word in words:
                self.send_body += struct.pack('>H', word)
            self.log.debug('send_body="BBH...", fc, count*2, word...')
            self.log.info(f'send_body={self.send_body}')
        else:
            self.exp_status = CONST.EXP_DATA_ADDRESS
            self.log.error(f'{CONST.EXP_DETAILS[self.exp_status]}, address={self.address}')

    def _01(self):
        self.prev_read_coils()
        if self.exp_status != CONST.EXP_NONE: return
        self._read_bits()
        self.after_read_coils()

    def _02(self):
        self.prev_read_discrete_inputs()
        if self.exp_status != CONST.EXP_NONE: return
        self._read_bits()
        self.after_read_discrete_inputs()

    def _03(self):
        self.prev_read_holding_registers()
        if self.exp_status != CONST.EXP_NONE: return
        self._read_registers()
        self.after_read_holding_registers()

    def _04(self):
        self.prev_read_input_registers()
        if self.exp_status != CONST.EXP_NONE: return
        self._read_registers()
        self.after_read_input_registers()

    def _05(self):
        self.prev_write_single_coil()
        if self.exp_status != CONST.EXP_NONE: return

        _bit_value = bool(self.value == 0xFF00)
        if self.DataBank[self.uid].set_bits(self.address, [_bit_value]):
            self.log.debug(f'write value={_bit_value}')
            self.send_body = struct.pack('>BHH', self.fc, self.address, self.value)
            self.log.debug(f'send_body=">BHH", fc, addr, value(convert value)')
            self.log.info(f'send_body={self.send_body}({_bit_value})')
        else:
            self.exp_status = CONST.EXP_DATA_ADDRESS
            self.log.error(f'{CONST.EXP_DETAILS[self.exp_status]}, '
                           f'address={self.address}, value={self.value}')

        self.after_write_single_coil()

    def _06(self):
        self.prev_write_single_register()
        if self.exp_status != CONST.EXP_NONE: return

        if self.DataBank[self.uid].set_words(self._address, [self.value]):
            self.log.debug(f'write value={self.value}')
            self.send_body = struct.pack('>BHH', self.fc, self.address, self.value)
            self.log.debug('send_body=">BHH", fc, addr, value')
            self.log.info(f'send_body={self.send_body}')
        else:
            self.exp_status = CONST.EXP_DATA_ADDRESS
            self.log.error(f'{CONST.EXP_DETAILS[self.exp_status]}, '
                           f'address={self.address}, value={self.value}')

        self.after_write_single_register()

    def _0f(self):
        self.prev_write_multiple_coils()
        if self.exp_status != CONST.EXP_NONE: return

        if self.DataBank[self.uid].set_bits(self.address, self.value):
            self.send_body = struct.pack('>BHH', self.fc, self.address, self.count)
            self.log.debug('send_body=">BHH", fc, address, count')
            self.log.info(f'send_body={self.send_body}')
        else:
            self.exp_status = CONST.EXP_DATA_ADDRESS
            self.log.error(f'{CONST.EXP_DETAILS[self.exp_status]}, '
                           f'address={self.address}, values={self.value}')

        self.after_write_multiple_coils()

    def _10(self):
        self.prev_write_multiple_registers()
        if self.exp_status != CONST.EXP_NONE: return

        if self.DataBank[self.uid].set_words(self._address, self.value):
            self.send_body = struct.pack('>BHH', self.fc, self.address, self.count)
            self.log.debug('send_body=">BHH", fc, address, count')
            self.log.info(f'send_body={self.send_body}')
        else:
            self.exp_status = CONST.EXP_DATA_ADDRESS
            self.log.error(f'{CONST.EXP_DETAILS[self.exp_status]}, '
                           f'address={self.address}, count={self.count}')

        self.after_write_multiple_registers()

    def modbus_processing(self):

        if self._chk_address() and self._chk_recv_etc():
            if self.fc is CONST.READ_COILS: self._01()
            elif self.fc is CONST.READ_DISCRETE_INPUTS: self._02()
            elif self.fc is CONST.READ_HOLDING_REGISTERS: self._03()
            elif self.fc is CONST.READ_INPUT_REGISTERS: self._04()
            elif self.fc is CONST.WRITE_SINGLE_COIL: self._05()
            elif self.fc is CONST.WRITE_SINGLE_REGISTER: self._06()
            elif self.fc is CONST.WRITE_MULTIPLE_COILS: self._0f()
            elif self.fc is CONST.WRITE_MULTIPLE_REGISTERS: self._10()
            else:
                self.exp_status = CONST.EXP_ILLEGAL_FUNCTION
                self.log.error(f'{CONST.EXP_DETAILS[self.exp_status]}, '
                               f'function code={self.fc}, address={self.address}')

        # 디바이스 에러 처리(ADDRESS, VALUE)
        if self.exp_status != CONST.EXP_NONE:
            self.send_body = struct.pack('BB', self.fc + 0x80, self.exp_status)
            self.log.debug('error send_body="BB", fc+0x80, exp_status')
            self.log.error(f'error send_body={self.send_body}')

        send_header = struct.pack('>HHHB',
                                  self.tid, self.pid, len(self.send_body)+1, self.uid)
        self.log.debug(f'send_head: "HHHB", tran_id, prot_id, len(send_body)+1, unit_id')
        self.log.info(f'send_head={send_header}')

        return send_header + self.send_body

    def prev_read_coils(self):
        pass

    def after_read_coils(self):
        pass

    def prev_read_discrete_inputs(self):
        pass

    def after_read_discrete_inputs(self):
        pass

    def prev_read_holding_registers(self):
        pass

    def after_read_holding_registers(self):
        pass

    def prev_read_input_registers(self):
        pass

    def after_read_input_registers(self):
        pass

    def prev_write_single_coil(self):
        pass

    def after_write_single_coil(self):
        pass

    def prev_write_single_register(self):
        pass

    def after_write_single_register(self):
        pass

    def prev_write_multiple_coils(self):
        pass

    def after_write_multiple_coils(self):
        pass

    def prev_write_multiple_registers(self):
        pass

    def after_write_multiple_registers(self):
        pass


    def _time_manager(self, data, uid):
        dict_key = f'{data["name"]}.{uid}'
        sys_time = datetime.now()

        dev_time_str = self.DataBank[uid].get_words(data['addr']-self.ws_addr,3)
        dev_time_fmt = f'{datetime.now()-timedelta(days=1):%Y-%m-%d} ' \
                       f'{dev_time_str[0]:02}:{dev_time_str[1]:02}:{dev_time_str[2]:02}'
        dev_time = datetime.strptime(dev_time_fmt, '%Y-%m-%d %H:%M:%S')
        diff_time = sys_time - dev_time

        self._sys_data[dict_key] = diff_time


    def _init_device(self):

        for i in range(self.device_info['unit_count']):
            for data in self.co + self.di:
                def_val = data['default']
                _bits = []
                if isinstance(def_val, int):
                    _bits.append(True if def_val else False)  # 1/0 변환
                elif isinstance(def_val, list):
                    for dv in def_val:
                        _bits.append(True if dv else False)
                else:
                    self.log.error(f'초기화 하려는 데이터 값에 오류가 있습니다. '
                                   f'데이터={def_val}({type(def_val)})')
                if _bits:   # 빈값이 아니면
                    self.DataBank[i].set_bits(data['addr'], _bits)
            for data in self.ir + self.hr:
                def_val = data['default']
                _words = []
                if isinstance(def_val, int):
                    _words.append(def_val)
                elif isinstance(def_val, list):
                    for dv in def_val:
                        _words.append(dv)
                else:
                    self.log.error(f'초기화 하려는 데이터 값에 오류가 있습니다. '
                                   f'데이터={def_val}({type(def_val)})')
                if _words:
                    self.DataBank[i].set_words(data['addr']-self.ws_addr, _words)
                if data.get('interval',0)>0 and data.get('type','')=='time':
                    self._time_manager(data, i)

        curr_time = datetime.now()
        for data in self.co + self.di + self.ir + self.hr:
            dict_key = data.get('interval', 0)
            if dict_key > 0: self.timer[dict_key] = curr_time


    def _gen_words_time(self, data, uid):
        curr_time = datetime.now()
        dict_key = f'{data["name"]}.{uid}'
        diff_time = self._sys_data[dict_key]
        dev_time = curr_time-diff_time
        words = [dev_time.hour, dev_time.minute, dev_time.second]
        self.DataBank[uid].set_words(data['addr']-self.ws_addr,words)

    def _gen_words_default(self, data, uid):
        min_val, max_val = data.get('min'), data.get('max')
        def_val = data.get('default')
        loop_cnt = 1 if isinstance(def_val, int) else len(def_val)
        for i in range(loop_cnt):
            word = randint(min_val, max_val)
            if random() > (100-data['error_rate'])/100.:
                word += max_val
            self.DataBank[uid].set_words(data['addr']+i-self.ws_addr, [word])

    def _gen_words(self, data, uid):
        data_type = data.get('type', '')
        if data_type == '':
            self._gen_words_default(data, uid)
        else:
            if data_type == 'time':
                self._gen_words_time(data, uid)
            else:
                pass

    def _show_console(self):
        cmd = 'cls' if os.name in ('nt', 'dos') else 'clear'
        os.system(cmd)

        print('MODBUS SIMULATOR.\n\n')
        print(f'{self.device_info["type"].upper()} - '
              f'{self.device_info["host"]}:{self.device_info["port"]}\n')

        disp_title = ['coils', 'discrete inputs', 'input registers', 'holding registers']
        proc_regs = [self.co, self.di, self.ir, self.hr]
        for regs_idx in range(len(proc_regs)):

            disp_msg = [disp_title[regs_idx].upper()]
            temp_msg = f'{"addr": >8} '
            for uid in range(self.device_info['unit_count']):
                _msg = f'uid={uid}'
                temp_msg += f'{_msg: >8} '
            disp_msg.append(temp_msg)

            for data_idx in range(len(proc_regs[regs_idx])):
                data = proc_regs[regs_idx][data_idx]
                addr = data['addr']
                def_val = data['default']

                if isinstance(def_val, int):
                    temp_msg = ''
                    for uid in range(self.device_info['unit_count']):
                        if regs_idx < 2:
                            value = self.DataBank[uid].get_bits(addr)[0]
                        else:
                            value = self.DataBank[uid].get_words(addr-self.ws_addr)[0]
                        temp_msg += f'{addr: >8} {value: >8} ' if uid == 0 else f'{value: >8} '
                    disp_msg.append(temp_msg)
                else:
                    temp_addr = addr
                    for _ in range(len(def_val)):
                        temp_msg = ''
                        for uid in range(self.device_info['unit_count']):
                            if regs_idx < 2:
                                value = self.DataBank[uid].get_bits(temp_addr)[0]
                            else:
                                value = self.DataBank[uid].get_words(temp_addr-self.ws_addr)[0]
                            temp_msg += f'{temp_addr: >8} {value: >8} ' if uid == 0 else f'{value: >8} '
                        disp_msg.append(temp_msg)
                        temp_addr += 1

            for msg in disp_msg:
                print(msg)
            print()

    def device_generation_data(self):

        curr_time = datetime.now()
        for i in range(self.device_info['unit_count']):
            for data in self.co + self.di:
                dict_key = data.get('interval', 0)
                if dict_key > 0:
                    diff_time = curr_time - self.timer[dict_key]
                    if diff_time.seconds >= dict_key:
                        def_val = data['default']
                        _bits = []
                        if isinstance(def_val, int):
                            _bits.append(True if randint(0,1) else False)
                        elif isinstance(def_val, list):
                            for _ in def_val:
                                _bits.append(True if randint(0,1) else False)
                        else:
                            pass
                        if _bits:  # 빈값이 아니면
                            self.DataBank[i].set_bits(data['addr'], _bits)

            for data in self.ir + self.hr:
                dict_key = data.get('interval', 0)
                if dict_key > 0:
                    diff_time = curr_time - self.timer[dict_key]
                    if diff_time.seconds >= dict_key:
                        self._gen_words(data, i)

        for k, v in self.timer.items():
            diff_time = curr_time - v
            if diff_time.seconds >= k:
                self.timer[k] = curr_time

        self._show_console()


class GenerationData(threading.Thread):

    def __init__(self, run_func, interval):
        super().__init__()
        self.Run = run_func
        self.interval = interval

    def run(self, *args):
        while True:
            self.Run()
            time.sleep(self.interval)


