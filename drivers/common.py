import os
import time
import struct
import threading
from datetime import datetime, timedelta
from random import randint, random

from slave import slave_constants as CONST
from slave.slave_utils import DataMgt, DataBank, TranInfo

class CommonDriver:

    def __init__(self, dev_info, log):
        self.di = dev_info
        self.log = log
        self.const = CONST

        self.DataBank = [DataBank()] * self.di.unit_cnt

        self.dd = {}            # device data
        self.ti = TranInfo()

        self.init_dev()

        gd_process = GenerationData(self.device_generation_data, self.di.itv)
        gd_process.daemon = True
        gd_process.start()


    def init_tran(self):
        self.ti.init()

    def chk_mbap_header(self, mbap_header):

        if not (mbap_header and len(mbap_header) == CONST.MBAP_HEAD_SIZE):
            if mbap_header != b'':  # connect(), close() 함수만 실행하면 b''값이 넘어옴
                self.log.error(f'MBAP_HEADER 데이터 오류: 길이({len(mbap_header)}), 데이터({mbap_header})')
            return 0

        (self.ti.tid, self.ti.pid, self.ti.len, self.ti.uid) = \
            struct.unpack('>HHHB', mbap_header)
        self.log.debug(f'mbap_header: '
                       f'transaction_id={self.ti.tid}, protocol_id={self.ti.pid}, '
                       f'data_length={self.ti.len}, unit_id={self.ti.uid}')

        if not ((self.ti.pid == 0) and
                (CONST.MIN_DATA_LEN < self.ti.len < CONST.MAX_DATA_LEN)):
            self.log.error(f'PROTOCOL ID 데이터 또는 DATA LENGTH 데이터 오류')
            return 0

        if self.ti.uid >= self.di.unit_cnt:
            self.log.error(f'지정한 UNIT 수를 초과했습니다. '
                           f'설정된 UNIT수={self.di.unit_cnt}, 요청 UNIT_ID={self.ti.uid}')
            return 0

        return self.ti.len

    def chk_receive_body(self, receive_body):

        if not (receive_body and (len(receive_body) == self.ti.len - 1)):
            self.log.error('수신된 데이터 또는 수신된 데이터의 길이가 요청한 데이터와 다릅니다.')
            return False

        self.ti.fc = struct.unpack('B', receive_body[:1])[0]
        self.ti.r_body = receive_body
        if self.ti.fc > CONST.MAX_FUNC_CODE:
            self.log.error(f'수신된 FUNCTION CODE{self.ti.fc}가 '
                           f'최대값인 {CONST.MAX_FUNC_CODE} 보다 큽니다.')
            return False

        return True

    def _chk_address(self):
        self.ti.addr = struct.unpack('>H', self.ti.r_body[1:3])[0]

        if self.ti.fc in (CONST.READ_COILS, CONST.WRITE_MULTIPLE_COILS, CONST.WRITE_SINGLE_COIL):
            self.ti.type, _base_addr = 0, CONST.MAX_BIT_CNT
        elif self.ti.fc is CONST.READ_DISCRETE_INPUTS:
            self.ti.type, _base_addr = 1, CONST.MAX_BIT_CNT
        elif self.ti.fc is CONST.READ_INPUT_REGISTERS:
            self.ti.type, _base_addr = 2, CONST.MAX_WORD_CNT
        elif self.ti.fc in (CONST.READ_HOLDING_REGISTERS, CONST.WRITE_SINGLE_REGISTER, CONST.WRITE_MULTIPLE_REGISTERS):
            self.ti.type, _base_addr = 3, CONST.MAX_WORD_CNT
        else: return False

        _s_addr, _e_addr, _b_addr, _m_addr = self.di.addr[self.ti.type][0], \
                                             self.di.addr[self.ti.type][1], \
                                             _base_addr, \
                                             self.di.addr[self.ti.type][2]
        if _s_addr <= self.ti.addr < (_e_addr - _b_addr):
            self.ti.m_addr = self.ti.addr - _m_addr
        else: return False

        return True

    def _chk_recv_etc(self):
        if self.ti.fc <= CONST.READ_INPUT_REGISTERS:
            self.ti.cnt = struct.unpack('>H', self.ti.r_body[3:])[0]
            self.log.debug(f'fc={self.ti.fc}, address={self.ti.addr}, count={self.ti.cnt}')
            if self.ti.fc in (CONST.READ_COILS, CONST.READ_DISCRETE_INPUTS):
                _min_value, _max_value = CONST.MIN_BIT_CNT, CONST.MAX_BIT_CNT
            else:
                _min_value, _max_value = CONST.MIN_WORD_CNT, CONST.MAX_WORD_CNT
            if not (_min_value <= self.ti.cnt <= _max_value):
                self.ti.es = CONST.EXP_DATA_VALUE
                self.log.error(f'{CONST.EXP_DETAILS[self.ti.es]}, count={self.ti.cnt}')
                return False
        elif self.ti.fc in (CONST.WRITE_SINGLE_COIL, CONST.WRITE_SINGLE_REGISTER):
            self.ti.value = struct.unpack('>H', self.ti.r_body[3:])[0]
            self.log.debug(f'fc={self.ti.fc}, address={self.ti.addr}, value={self.ti.value}')
        else:
            (self.ti.cnt, self.ti.b_cnt) = struct.unpack('>HB', self.ti.r_body[3:6])
            self.log.debug(f'fc={self.ti.fc}, address={self.ti.addr}, '
                           f'count={self.ti.cnt}, byte_count={self.ti.b_cnt}')
            if self.ti.fc is CONST.WRITE_MULTIPLE_COILS:
                _min_value, _max_value, _chk_value = \
                    CONST.MIN_BIT_CNT, CONST.MAX_BIT_0F_CNT, self.ti.cnt / 8
                self.ti.value = [False] * self.ti.cnt
                for i, item in enumerate(self.ti.value):
                    bit_pos = int(i / 8) + 6
                    bit_value = struct.unpack('B', self.ti.r_body[bit_pos:bit_pos + 1])[0]
                    self.ti.value[i] = DataMgt.test_bit(bit_value, i % 8)
                self.log.debug(f'write value={self.ti.value}')
            else:
                _min_value, _max_value, _chk_value = \
                    CONST.MIN_WORD_CNT, CONST.MAX_WORD_10_CNT, self.ti.cnt * 2
                self.ti.value = [0] * self.ti.cnt
                for i, item in enumerate(self.ti.value):
                    word_offset = i * 2 + 6
                    self.ti.value[i] = struct.unpack('>H', self.ti.r_body[word_offset:word_offset + 2])[0]
                self.log.debug(f'write values={self.ti.value}')
            if not (_min_value <= self.ti.cnt <= _max_value and self.ti.b_cnt >= _chk_value):
                self.ti.es = CONST.EXP_DATA_VALUE
                self.log.error(f'{CONST.EXP_DETAILS[self.ti.es]}, count={self.ti.cnt}')
                return False
        return True

    def _read_bits(self):
        bits = self.DataBank[self.ti.uid].get_bits(self.ti.m_addr, self.ti.cnt)
        self.log.debug(f'return value(s)={bits}')
        if bits:
            byte_size = round(self.ti.cnt / 8 + .5)  # bit수를 8로 나누고 나머지가 있으면 1 추가
            byte_list = [0] * byte_size
            for i, item in enumerate(bits):
                if item:
                    byte_pos = int(i / 8)
                    byte_list[byte_pos] = DataMgt.set_bit(byte_list[byte_pos], i % 8)
            self.ti.s_body = struct.pack('BB', self.ti.fc, len(byte_list))
            for byte in byte_list:
                self.ti.s_body += struct.pack('B', byte)
            self.log.debug('send_body="BBB...", fc, len(byte_list), byte...')
            self.log.info(f'send_body={self.ti.s_body}')
        else:
            self.ti.es = CONST.EXP_DATA_ADDRESS
            self.log.error(f'{CONST.EXP_DETAILS[self.ti.es]}, '
                           f'address={self.ti.addr}, get_bits={bits}')

    def _read_registers(self):
        words = self.DataBank[self.ti.uid].get_words(self.ti.m_addr, self.ti.cnt)
        self.log.debug(f'return values={words}')
        if words:
            self.ti.s_body = struct.pack('BB', self.ti.fc, self.ti.cnt * 2)
            for word in words:
                self.ti.s_body += struct.pack('>H', word)
            self.log.debug('send_body="BBH...", fc, count*2, word...')
            self.log.info(f'send_body={self.ti.s_body}')
        else:
            self.ti.es = CONST.EXP_DATA_ADDRESS
            self.log.error(f'{CONST.EXP_DETAILS[self.ti.es]}, address={self.ti.addr}')

    def _01(self):
        self.prev_read_coils()
        if self.ti.es != CONST.EXP_NONE: return
        self._read_bits()
        self.after_read_coils()

    def _02(self):
        self.prev_read_discrete_inputs()
        if self.ti.es != CONST.EXP_NONE: return
        self._read_bits()
        self.after_read_discrete_inputs()

    def _03(self):
        self.prev_read_holding_registers()
        if self.ti.es != CONST.EXP_NONE: return
        self._read_registers()
        self.after_read_holding_registers()

    def _04(self):
        self.prev_read_input_registers()
        if self.ti.es != CONST.EXP_NONE: return
        self._read_registers()
        self.after_read_input_registers()

    def _05(self):
        self.prev_write_single_coil()
        if self.ti.es != CONST.EXP_NONE: return

        _bit_value = bool(self.ti.value == 0xFF00)
        if self.DataBank[self.ti.uid].set_bits(self.ti.m_addr, [_bit_value]):
            self.log.debug(f'write value={_bit_value}')
            self.ti.s_body = struct.pack('>BHH', self.ti.fc, self.ti.addr, self.ti.value)
            self.log.debug(f'send_body=">BHH", fc, addr, value(convert value)')
            self.log.info(f'send_body={self.ti.s_body}({_bit_value})')
        else:
            self.ti.es = CONST.EXP_DATA_ADDRESS
            self.log.error(f'{CONST.EXP_DETAILS[self.ti.es]}, '
                           f'address={self.ti.addr}, value={self.ti.value}')

        self.after_write_single_coil()

    def _06(self):
        self.prev_write_single_register()
        if self.ti.es != CONST.EXP_NONE: return

        if self.DataBank[self.ti.uid].set_words(self.ti.m_addr, [self.ti.value]):
            self.log.debug(f'write value={self.ti.value}')
            self.ti.s_body = struct.pack('>BHH', self.ti.fc, self.ti.addr, self.ti.value)
            self.log.debug('send_body=">BHH", fc, addr, value')
            self.log.info(f'send_body={self.ti.s_body}')
        else:
            self.ti.es = CONST.EXP_DATA_ADDRESS
            self.log.error(f'{CONST.EXP_DETAILS[self.ti.es]}, '
                           f'address={self.ti.addr}, value={self.ti.value}')

        self.after_write_single_register()

    def _0f(self):
        self.prev_write_multiple_coils()
        if self.ti.es != CONST.EXP_NONE: return

        if self.DataBank[self.ti.uid].set_bits(self.ti.m_addr, self.ti.value):
            self.ti.s_body = struct.pack('>BHH', self.ti.fc, self.ti.addr, self.ti.cnt)
            self.log.debug('send_body=">BHH", fc, address, count')
            self.log.info(f'send_body={self.ti.s_body}')
        else:
            self.ti.es = CONST.EXP_DATA_ADDRESS
            self.log.error(f'{CONST.EXP_DETAILS[self.ti.es]}, '
                           f'address={self.ti.addr}, values={self.ti.value}')

        self.after_write_multiple_coils()

    def _10(self):
        self.prev_write_multiple_registers()
        if self.ti.es != CONST.EXP_NONE: return

        if self.DataBank[self.ti.uid].set_words(self.ti.m_addr, self.ti.value):
            self.ti.s_body = struct.pack('>BHH', self.ti.fc, self.ti.addr, self.ti.cnt)
            self.log.debug('send_body=">BHH", fc, address, count')
            self.log.info(f'send_body={self.ti.s_body}')
        else:
            self.ti.es = CONST.EXP_DATA_ADDRESS
            self.log.error(f'{CONST.EXP_DETAILS[self.ti.es]}, '
                           f'address={self.ti.addr}, count={self.ti.cnt}')

        self.after_write_multiple_registers()

    def modbus_processing(self):

        if self._chk_address() and self._chk_recv_etc():
            if self.ti.fc is CONST.READ_COILS: self._01()
            elif self.ti.fc is CONST.READ_DISCRETE_INPUTS: self._02()
            elif self.ti.fc is CONST.READ_HOLDING_REGISTERS: self._03()
            elif self.ti.fc is CONST.READ_INPUT_REGISTERS: self._04()
            elif self.ti.fc is CONST.WRITE_SINGLE_COIL: self._05()
            elif self.ti.fc is CONST.WRITE_SINGLE_REGISTER: self._06()
            elif self.ti.fc is CONST.WRITE_MULTIPLE_COILS: self._0f()
            elif self.ti.fc is CONST.WRITE_MULTIPLE_REGISTERS: self._10()
            else:
                self.ti.es = CONST.EXP_ILLEGAL_FUNCTION
                self.log.error(f'{CONST.EXP_DETAILS[self.ti.es]}, '
                               f'function code={self.ti.fc}, address={self.ti.addr}')

        # 디바이스 에러 처리(ADDRESS, VALUE)
        if self.ti.es != CONST.EXP_NONE:
            self.ti.s_body = struct.pack('BB', self.ti.fc + 0x80, self.ti.es)
            self.log.debug('error send_body="BB", fc+0x80, exp_status')
            self.log.error(f'error send_body={self.ti.s_body}')

        send_header = struct.pack('>HHHB',
                                  self.ti.tid, self.ti.pid, len(self.ti.s_body)+1, self.ti.uid)
        self.log.debug(f'send_head: "HHHB", tran_id, prot_id, len(send_body)+1, unit_id')
        self.log.info(f'send_head={send_header}')

        return send_header + self.ti.s_body

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

        dev_time_str = self.DataBank[uid].get_words(data['addr']-self.di.w_addr,3)
        dev_time_fmt = f'{datetime.now()-timedelta(days=1):%Y-%m-%d} ' \
                       f'{dev_time_str[0]:02}:{dev_time_str[1]:02}:{dev_time_str[2]:02}'
        dev_time = datetime.strptime(dev_time_fmt, '%Y-%m-%d %H:%M:%S')
        diff_time = sys_time - dev_time

        self.dd[dict_key] = diff_time


    def _init_dev(self):

        for i in range(self.di.unit_cnt):
            for data in self.di.data[0] + self.di.data[1]:
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
            for data in self.di.data[2] + self.di.data[3]:
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
                    self.DataBank[i].set_words(data['addr']-self.di.w_addr, _words)

                if data.get('interval',0)>0 and data.get('type','')=='time':
                    self._time_manager(data, i)

        curr_time = datetime.now()
        for i in range(len(self.di.data)):
            for data in self.di.data[i]:
                d_key = data.get('interval', 0)
                if d_key > 0: self.dd['timer'][d_key] = curr_time

    def _gen_words_time(self, data, uid):
        curr_time = datetime.now()
        dict_key = f'{data["name"]}.{uid}'
        diff_time = self.dd[dict_key]
        dev_time = curr_time-diff_time
        words = [dev_time.hour, dev_time.minute, dev_time.second]
        self.DataBank[uid].set_words(data['addr']-self.di.w_addr,words)

    def _gen_words_default(self, data, uid):
        min_val, max_val = data.get('min'), data.get('max')
        def_val = data.get('default')
        loop_cnt = 1 if isinstance(def_val, int) else len(def_val)
        for i in range(loop_cnt):
            (_min, _max) = (min_val, max_val) if loop_cnt == 1 else (min_val[i], max_val[i])
            word = randint(_min, _max)
            if random() > (100-data['error_rate'])/100.:
                word += _max
            self.DataBank[uid].set_words(data['addr']+i-self.di.w_addr, [word])

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

        if not self.di.no_disp: return

        cmd = 'cls' if os.name in ('nt', 'dos') else 'clear'
        os.system(cmd)

        print('MODBUS SIMULATOR.\n\n')
        print(f'{self.di.type.upper()} - {self.di.host}:{self.di.port}\n')

        disp_title = ['coils', 'discrete inputs', 'input registers', 'holding registers']
        for regs_idx in range(len(self.di.data)):

            disp_msg = [disp_title[regs_idx].upper()]
            temp_msg = f'{"addr": >8} '
            for uid in range(self.di.unit_cnt):
                _msg = f'uid={uid}'
                temp_msg += f'{_msg: >8} '
            disp_msg.append(temp_msg)

            for data_idx in range(len(self.di.data[regs_idx])):
                data = self.di.data[regs_idx][data_idx]
                addr = data['addr']
                def_val = data['default']

                if isinstance(def_val, int):
                    temp_msg = ''
                    for uid in range(self.di.unit_cnt):
                        if regs_idx < 2:
                            value = self.DataBank[uid].get_bits(addr)[0]
                        else:
                            value = self.DataBank[uid].get_words(addr-self.di.w_addr)[0]
                        temp_msg += f'{addr: >8} {value: >8} ' if uid == 0 else f'{value: >8} '
                    disp_msg.append(temp_msg)
                else:
                    temp_addr = addr
                    for _ in range(len(def_val)):
                        temp_msg = ''
                        for uid in range(self.di.unit_cnt):
                            if regs_idx < 2:
                                value = self.DataBank[uid].get_bits(temp_addr)[0]
                            else:
                                value = self.DataBank[uid].get_words(temp_addr-self.di.w_addr)[0]
                            temp_msg += f'{temp_addr: >8} {value: >8} ' if uid == 0 else f'{value: >8} '
                        disp_msg.append(temp_msg)
                        temp_addr += 1

            for msg in disp_msg:
                print(msg)
            print()

    def device_generation_data(self):

        curr_time = datetime.now()
        for i in range(self.di.unit_cnt):
            for data in self.di.data[0] + self.di.data[1]:
                dict_key = data.get('interval', 0)
                if dict_key > 0:
                    diff_time = curr_time - self.dd['timer'][dict_key]
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

            for data in self.di.data[2] + self.di.data[3]:
                dict_key = data.get('interval', 0)
                if dict_key > 0:
                    diff_time = curr_time - self.dd['timer'][dict_key]
                    if diff_time.seconds >= dict_key:
                        self._gen_words(data, i)

        for k, v in self.dd['timer'].items():
            diff_time = curr_time - v
            if diff_time.seconds >= k:
                self.dd['timer'][k] = curr_time

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
