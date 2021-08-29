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

        self.DataBank = [DataBank(self.di.b_cnt, self.di.w_cnt)
                         for _ in range(self.di.unit_cnt)]

        self.dd = {}            # device data
        self.ti = TranInfo()

        self._init_dev()

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
                self.ti.em = f'count={self.ti.cnt}'
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
                self.ti.em = f'count={self.ti.cnt}'
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
            self.ti.em = f'get_bits={bits}'

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

    def _01(self):
        self._prev_read_coils()
        if self.ti.es != CONST.EXP_NONE: return
        self._read_bits()
        self._after_read_coils()

    def _02(self):
        self._prev_read_discrete_inputs()
        if self.ti.es != CONST.EXP_NONE: return
        self._read_bits()
        self._after_read_discrete_inputs()

    def _03(self):
        self.log.warning('aaaa')
        self._prev_read_holding_registers()
        self.log.warning('bbbb')

        if self.ti.es != CONST.EXP_NONE: return
        self.log.warning('cccc')
        self._read_registers()
        self.log.warning('dddd')
        self._after_read_holding_registers()
        self.log.warning('eeee')

    def _04(self):
        self._prev_read_input_registers()
        if self.ti.es != CONST.EXP_NONE: return
        self._read_registers()
        self._after_read_input_registers()

    def _05(self):
        self._prev_write_single_coil()
        if self.ti.es != CONST.EXP_NONE: return

        _bit_value = bool(self.ti.value == 0xFF00)
        if self.DataBank[self.ti.uid].set_bits(self.ti.m_addr, [_bit_value]):
            self.log.debug(f'write value={_bit_value}')
            self.ti.s_body = struct.pack('>BHH', self.ti.fc, self.ti.addr, self.ti.value)
            self.log.debug(f'send_body=">BHH", fc, addr, value(convert value)')
            self.log.info(f'send_body={self.ti.s_body}({_bit_value})')
        else:
            self.ti.es = CONST.EXP_DATA_ADDRESS
            self.ti.em = f'value={self.ti.value}'

        self._after_write_single_coil()

    def _06(self):
        self._prev_write_single_register()
        if self.ti.es != CONST.EXP_NONE: return

        if self.DataBank[self.ti.uid].set_words(self.ti.m_addr, [self.ti.value]):
            self.log.debug(f'write value={self.ti.value}')
            self.ti.s_body = struct.pack('>BHH', self.ti.fc, self.ti.addr, self.ti.value)
            self.log.debug('send_body=">BHH", fc, addr, value')
            self.log.info(f'send_body={self.ti.s_body}')
        else:
            self.ti.es = CONST.EXP_DATA_ADDRESS
            self.ti.em = f'value={self.ti.value}'

        self._after_write_single_register()

    def _0f(self):
        self._prev_write_multiple_coils()
        if self.ti.es != CONST.EXP_NONE: return

        if self.DataBank[self.ti.uid].set_bits(self.ti.m_addr, self.ti.value):
            self.ti.s_body = struct.pack('>BHH', self.ti.fc, self.ti.addr, self.ti.cnt)
            self.log.debug('send_body=">BHH", fc, address, count')
            self.log.info(f'send_body={self.ti.s_body}')
        else:
            self.ti.es = CONST.EXP_DATA_ADDRESS
            self.ti.em = f'values={self.ti.value}'

        self._after_write_multiple_coils()

    def _10(self):
        self._prev_write_multiple_registers()
        if self.ti.es != CONST.EXP_NONE: return

        if self.DataBank[self.ti.uid].set_words(self.ti.m_addr, self.ti.value):
            self.ti.s_body = struct.pack('>BHH', self.ti.fc, self.ti.addr, self.ti.cnt)
            self.log.debug('send_body=">BHH", fc, address, count')
            self.log.info(f'send_body={self.ti.s_body}')
        else:
            self.ti.es = CONST.EXP_DATA_ADDRESS
            self.ti.em = f'count={self.ti.cnt}'

        self._after_write_multiple_registers()

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

        # 디바이스 에러 처리(ADDRESS, VALUE)
        if self.ti.es != CONST.EXP_NONE:
            self.log.error(f'{CONST.EXP_TXT[self.ti.es]}, '
                           f'fc={self.ti.fc}, addr={self.ti.addr}'
                           f'{", "+self.ti.em if self.ti.em != "" else self.ti.em}')
            self.ti.s_body = struct.pack('BB', self.ti.fc + 0x80, self.ti.es)
            self.log.debug('error send_body="BB", fc+0x80, exp_status')
            self.log.error(f'error send_body={self.ti.s_body}')

        send_header = struct.pack('>HHHB',
                                  self.ti.tid, self.ti.pid,
                                  len(self.ti.s_body)+1, self.ti.uid)
        self.log.debug(f'send_head: "HHHB", tran_id, prot_id, '
                       f'len(send_body)+1, unit_id')
        self.log.info(f'send_head={send_header}')

        return send_header + self.ti.s_body

    def _prev_read_coils(self):
        pass

    def _after_read_coils(self):
        pass

    def _prev_read_discrete_inputs(self):
        pass

    def _after_read_discrete_inputs(self):
        pass

    def _prev_read_holding_registers(self):
        pass

    def _after_read_holding_registers(self):
        pass

    def _prev_read_input_registers(self):
        pass

    def _after_read_input_registers(self):
        pass

    def _prev_write_single_coil(self):
        pass

    def _after_write_single_coil(self):
        pass

    def _prev_write_single_register(self):
        pass

    def _after_write_single_register(self):
        pass

    def _prev_write_multiple_coils(self):
        pass

    def _after_write_multiple_coils(self):
        pass

    def _prev_write_multiple_registers(self):
        pass

    def _after_write_multiple_registers(self):
        pass


    def _time_manager(self, data, uid):
        """
        주기적으로 변경되는 디바이스의 시간정보 계산을 위해,
        해당 레지스터의 시간정보 초기 설정값(또는 변경된 설정값)과 시스템의 시간정보 차이를 저장하여,
        주기적으로 변경되는 디바이스의 시간정보를 계산

        :param data: 주기적으로 변경되는 시간정보를 포함하는 레지스터(IR쪽)
        :param uid: 해당 레지스터의 Unit-ID(Unit-ID 별로 시간값을 변경할 수 있기 때문에 분리)
        :return: 없음
        """

        # 레지스터 이름과 Unit-ID를 이용해 딕셔너리 key 생성(ex: curr_time.4)
        dict_key = f'{data["name"]}.{uid}'
        # 설정값과의 시간차 계산을 위해 시스템의 현재 시간 구함
        sys_time = datetime.now()

        # 현재 해당 레지스터(이름과 Unit-ID로 접근 가능한)의 값을 읽어옴(디바이스 시간)
        # 시간은 '시', '분', '초' 3개로 관리됨(그래서 읽어 들이는 갯 수를 나타내는 가장 마지막은 3)
        dev_time_str = self.DataBank[uid].get_words(data['addr']-self.di.w_addr,3)
        # 문자형 데이터인 시간을 시간 데이터로 변환
        # 시간 데이터로 변환할 때, '시분초'정보만 있기 때문에 하루 전 시간과 현재 시간을 비교함
        # 시간 차 정보를 항상 양수로 관리하기 위해 하루 전 시간과 비교함
        dev_time_fmt = f'{datetime.now()-timedelta(days=1):%Y-%m-%d} ' \
                       f'{dev_time_str[0]:02}:{dev_time_str[1]:02}:{dev_time_str[2]:02}'
        dev_time = datetime.strptime(dev_time_fmt, '%Y-%m-%d %H:%M:%S')
        diff_time = sys_time - dev_time

        self.dd['timer'][dict_key] = diff_time


    def _init_dev(self):
        """
        설정파일의 레지스터 'default' 정보를 이용해 디바이스를 초기화 한다.
        :return: 없음
        """

        # 디바이스 데이터 저장 영역(self.dd)에 시간정보 저장 공간 확보
        self.dd['timer'] = {}

        # 디바이스의 unit 갯 수 만큼 반복 처리
        for i in range(self.di.unit_cnt):

            # 디바이스의 bit(s) 영역(CO/DI) 정보 초기화
            for data in self.di.data[CONST.DATA_CO] + self.di.data[CONST.DATA_DI]:

                # 초기화 할 bit의 기본값을 읽어 옴
                def_val = data.get('default', 0)    # 값이 없으면 False
                # 기본값을 저장할 변수
                _bits = []
                # 기본값이 정수(하나의 값으로 이뤄진 bit)이면
                if isinstance(def_val, int):
                    _bits.append(True if def_val else False)  # 1/0 변환
                elif isinstance(def_val, list):
                    for dv in def_val:
                        _bits.append(True if dv else False)
                else:
                    self.log.error(f'초기화 하려는 데이터 값에 오류가 있습니다. '
                                   f'데이터={def_val}({type(def_val)})')
                # 값이 존재하면 메모리에 저장
                if _bits:
                    self.DataBank[i].set_bits(data['addr'], _bits)

            # 디바이스 레지스터 영역(IR/HR) 정보 초기화
            for data in self.di.data[CONST.DATA_IR] + self.di.data[CONST.DATA_HR]:

                # 초기값 읽어옴(없으면 0으로 초기화)
                def_val = data.get('default', 0)
                _words = []
                if isinstance(def_val, int):
                    _words.append(def_val)
                elif isinstance(def_val, list):
                    for dv in def_val:
                        _words.append(dv)
                else:
                    self.log.error(f'초기화 하려는 데이터 값에 오류가 있습니다. '
                                   f'데이터={def_val}({type(def_val)})')
                # 값이 존재하면 메모리에 저장
                if _words:
                    self.DataBank[i].set_words(data['addr']-self.di.w_addr, _words)

                # 데이터 타입별 개별 처리 영역
                #
                # 데이터 타입 - 'time' 처리
                # - 시간정보 계산을 위해 시스템의 현재 시간과 디바이스에 설정된 시간정보의 차이를 저장해,
                #   디바이스의 시간정보를 계산하는데 사용함

                # 주기적으로 변경할 데이터중에 타입이 'time'이면 시간차이를 저장하기 위해 함수 호출
                if data.get('interval',0)>0 and data.get('type','')=='time':
                    self._time_manager(data, i)

        # 주기적으로 변경할 데이터의 변경시간 점검을 위해 시간정보 저장
        self.dd['interval'] = {}        # 저장공간 확보
        curr_time = datetime.now()      # 저장할 현재 시스템시간 계산
        # CO/DI/IR/HR 순차적 처리(Unit-ID와 관계없음)
        for i in range(len(self.di.data)):
            for data in self.di.data[i]:
                # 변경 시간을 key로 해서 저장함
                # 변경 시간(key)보다 시간차(저장시간(=직전 변경시간)-현재시간)가 크면 값을 갱신함
                d_key = data.get('interval', 0)
                # 변경 주기가 0보다 큰 값만 저장
                if d_key > 0: self.dd['interval'][d_key] = curr_time

    def _gen_words_time(self, data, uid):
        """
        시간 데이터 생성
          - 시간 데이터는 시스템 시간과 시간차(설정시점의 시스템 시간 - 설정시간)를 이용해 생성
        :param data: 변경할 레지스터 정보
        :param uid: 변경할 unit-id 정보
        :return: 없음
        """

        # 현재 시스템 시간 구함(시간차를 빼서 레지스터 시간 정보 구함)
        curr_time = datetime.now()
        # 현재 레지스터의 시간차 정보를 구하기 위해 딕셔너리 key 생성 후 시간차 구함
        dict_key = f'{data["name"]}.{uid}'
        diff_time = self.dd['timer'][dict_key]
        # 기기 현재시간 설정(시스템 현재시간 - 시간차)
        dev_time = curr_time - diff_time
        # 기기 현재시간 저장
        words = [dev_time.hour, dev_time.minute, dev_time.second]
        self.DataBank[uid].set_words(data['addr']-self.di.w_addr,words)

    def _gen_words_default(self, data, uid):
        """
        일반적인 데이터(데이터 타입 없고, min/max값으로 구성된 데이터) 생성
        :param data: 변경할 레지스터 정보
        :param uid: 변경할 unit-id 정보
        :return: 없음
        """

        # 정보를 생성하기 위한 min/max값 구함
        min_val, max_val = data.get('min'), data.get('max')
        # 변경할 데이터 갯 수 계산(=해당 레지스터의 default값의 갯 수)
        def_val = data.get('default')
        loop_cnt = 1 if isinstance(def_val, int) else len(def_val)
        for i in range(loop_cnt):
            (_min, _max) = (min_val, max_val) if loop_cnt == 1 else (min_val[i], max_val[i])
            word = randint(_min, _max)
            # 에러율(error_rate)가 없으면 0으로 처리
            if random() > (100-data.get('error_rate', 0))/100.:
                # 에러일 경우 생성한 랜덤값에 max값을 더함
                # 에러 데이터가 별로 중요하지 않아 간단하게 처리함
                word += _max
            # 주소를 증가하며, 하나씩 메모리에 저장
            self.DataBank[uid].set_words(data['addr']+i-self.di.w_addr, [word])

    def _gen_words(self, data, uid):
        """
        데이터 타입별로 데이터 생성
        :param data: 데이터 생성 레지스터 정보
        :param uid: 데이터 생성 unit-id
        :return: 없음
        """

        # 해당 레지스터의 데이터 타입 가져옴(없으면 '')
        data_type = data.get('type', '')

        # 데이터 타이별로 데이터 생성
        # 별도 타입이 없는 경우
        if data_type == '':
            self._gen_words_default(data, uid)
        # 데이터 타입이 'time'인 경우
        elif data_type == 'time':
            self._gen_words_time(data, uid)
        # 데이터 타입 추가를 위해 남겨둠
        else:
            pass

    def _show_console(self):

        if self.di.no_disp: return

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
        """
        설정파일의 레지스터 갱신주기 정보를 이용해 레지스터의 데이터를 생성한다.
        :return: 없음
        """

        # 데이터 갱신 주기를 비교할 현재 시간을 저장
        curr_time = datetime.now()

        # 디바이스의 unit 갯 수 만큼 반복 처리
        for i in range(self.di.unit_cnt):

            # CO/DI 정보 처리
            for data in self.di.data[CONST.DATA_CO] + self.di.data[CONST.DATA_DI]:
                # 각 레지스터의 데이터 갱신주기 정보(interval)를 읽음(없으면 0)
                dict_key = data.get('interval', 0)
                # 데이터 갱신주기가 있으면, 데이터 갱신작업 수행
                if dict_key > 0:
                    # 시간차 계산
                    diff_time = curr_time - self.dd['interval'][dict_key]
                    # 시간차가 갱신주기(dict_key=data(interval)) 보다 크면, 데이터 갱신
                    if diff_time.seconds >= dict_key:
                        # 변경할 갯 수 확인을 위해 default값 읽음
                        def_val = data['default']
                        # 저장할 변수 선언
                        bits = []
                        if isinstance(def_val, int):
                            bits.append(True if randint(0,1) else False)
                        elif isinstance(def_val, list):
                            for _ in def_val:
                                bits.append(True if randint(0,1) else False)
                        else:
                            pass
                        if bits:  # 빈값이 아니면
                            self.DataBank[i].set_bits(data['addr'], bits)

            # IR/HR 레지스터 처리
            for data in self.di.data[CONST.DATA_IR] + self.di.data[CONST.DATA_HR]:
                dict_key = data.get('interval', 0)
                if dict_key > 0:
                    diff_time = curr_time - self.dd['interval'][dict_key]
                    # 시간차가 갱신주기보다 크면 레지스터 갱신작업 수행
                    if diff_time.seconds >= dict_key:
                        self._gen_words(data, i)

        # 갱신시간 저장
        for k, v in self.dd['interval'].items():
            # 갱신 시간차 계산(v(=value)는 직전 갱신 시간
            diff_time = curr_time - v
            # 시간차와 k(=key, 갱신주기) 값 비교,
            # 시간차가 갱신주기보다 크면, 갱신 시간 변경
            if diff_time.seconds >= k:
                self.dd['interval'][k] = curr_time

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
