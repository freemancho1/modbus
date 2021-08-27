import struct
from threading import Lock


class DevInfo:

    def __init__(self):
        self.host           = ''
        self.port           = ''
        self.type           = ''    # device type
        self.unit_cnt       = 0
        self.no_disp        = None
        self.log_level      = ''
        self.drv            = ''
        self.itv            = 0     # interval

        # 2차원 배열 - 0:co, 1:di, 2:ir, 3:hr
        self.addr           = []    # 0:start, 1:end, 2:base
        self.w_addr         = 0     # device 별 레지스터 초기 주소설정값
        self.data           = []    # {}

    def __str__(self):
        return f'{self.type}:{self.host}:{self.port}[{self.unit_cnt}], ' \
               f'no_disp={self.no_disp}, log_level={self.log_level}, ' \
               f'interval={self.itv}\ndrive path: {self.drv_path}\n' \
               f'addr: {self.addr}\ndata:\n{self.data}'

    def get_title(self):
        return f'{self.type}:{self.host}:{self.port}'


class TranInfo:

    def __init__(self):
        self.tid            = 0
        self.pid            = 0
        self.len            = 0
        self.uid            = 0
        self.fc             = 0
        self.type           = 0     # data(coil, registers) type
        self.addr           = 0
        self.m_addr          = 0     # memory address
        self.cnt            = 0
        self.b_cnt          = 0     # byte count
        self.value          = 0
        self.es             = 0x00  # exp_status
        self.r_body         = b''
        self.s_body         = b''

    def init(self):
        self.tid            = 0
        self.pid            = 0
        self.len            = 0
        self.uid            = 0
        self.fc             = 0
        self.type           = 0     # data(coil, registers) type
        self.addr           = 0
        self._addr          = 0     # memory address
        self.cnt            = 0
        self.b_cnt          = 0     # byte count
        self.value          = 0
        self.es             = 0x00  # exp_status
        self.r_head         = b''
        self.r_body         = b''
        self.s_head         = b''
        self.s_body         = b''


class DataBank:

    def __init__(self):
        self.bits_lock = Lock()
        self.bits = [False] * 20000   # 00000~09999(Coils), 10000~19999(Discrete Inputs)
        self.words_lock = Lock()
        self.words = [0] * 20000      # 00000~09999(Input Register), 10000~19999(Holding Register)

    def get_bits(self, address, number=1):
        with self.bits_lock:
            if (address >= 0) and (address + number <= len(self.bits)):
                return self.bits[address:address+number]
            else:
                return None

    def set_bits(self, address, bit_list):
        result = None
        bit_list = [bool(b) for b in bit_list]
        with self.bits_lock:
            if (address >= 0) and (address+len(bit_list) <= len(self.bits)):
                self.bits[address:address+len(bit_list)] = bit_list
                result = True
        return result

    def get_words(self, address, number=1):
        with self.words_lock:
            if (address >= 0) and (address+number <= len(self.words)):
                return self.words[address:address+number]
            else:
                return None

    def set_words(self, address, word_list):
        result = None
        word_list = [int(w) & 0xffff for w in word_list]
        with self.words_lock:
            if (address >= 0) and (address+len(word_list) <= len(self.words)):
                self.words[address:address+len(word_list)] = word_list
                result = True
        return result


class DataMgt:

    @staticmethod
    def get_bits_from_int(int_value, value_size=16):
        bits = []
        for i in range(value_size):
            bits.append(bool((int_value >> i) & 0x01))
        return bits

    # short alias
    int2bits = get_bits_from_int

    @staticmethod
    def test_bit(value, offset):
        mask = 1 << offset
        return bool(value & mask)

    @staticmethod
    def set_bit(value, offset):
        mask = 1 << offset
        return int(value | mask)

    @staticmethod
    def reset_bit(value, offset):
        mask = ~(1 << offset)
        return int(value & mask)

    @staticmethod
    def toggle_bit(value, offset):
        mask = 1 << offset
        return int(value ^ mask)

    @staticmethod
    def get_long_from_word_list(word_list, big_endian=True, double_words=False):
        long_list = []
        block_size = 4 if double_words else 2

        for idx in range(int(len(word_list) / block_size)):
            start = block_size * idx
            long_data = 0
            if big_endian:
                if double_words:
                    long_data += (word_list[start] << 48) + (word_list[start+1] << 32) + \
                                 (word_list[start+2] << 16) + word_list[start+3]
                else:
                    long_data += (word_list[start] << 16) + word_list[start+1]
            else:
                if double_words:
                    long_data += (word_list[start+3] << 48) + (word_list[start+2] << 32)
                long_data += (word_list[start+1] << 16) + word_list[start]
            long_list.append(long_data)

        return long_list

    # short alias
    words2longs = get_long_from_word_list

    @staticmethod
    def get_word_from_long_list(long_list, big_endian=True, double_long=False):
        word_list = []
        temp_words = []
        for long_data in long_list:
            temp_words.clear()
            temp_words.append(long_data & 0xffff)
            temp_words.append((long_data >> 16) & 0xffff)
            if double_long:
                temp_words.append((long_data >> 32) & 0xffff)
                temp_words.append((long_data >> 48) & 0xffff)
            if big_endian:
                temp_words.reverse()
            word_list.append(temp_words)
        return word_list

    # short alias
    longs2words = get_word_from_long_list

    @staticmethod
    def get_2comp(int_value, value_size=16):
        if not -1 << value_size-1 <= int_value < 1 << value_size:
            err_msg = f'could not compute two\'s complement for {int_value} on {value_size} bits'
            raise ValueError(err_msg)
        if int_value < 0:
            int_value += 1 << value_size
        elif int_value & (1 << (value_size - 1)):
            int_value -= 1 << value_size
        return int_value

    # short alias
    twos_c = get_2comp

    @staticmethod
    def get_list_2comp(value_list, value_size=16):
        return [DataMgt.get_2comp(value, value_size) for value in value_list]

    twos_c_l = get_list_2comp

    @staticmethod
    def decode_i3e(int_value, double=False):
        if double:
            return struct.unpack('d', struct.pack('Q', int_value))[0]
        else:
            return struct.unpack('f', struct.pack('I', int_value))[0]

    @staticmethod
    def encode_i3e(float_value, double=False):
        if double:
            return struct.unpack('Q', struct.pack('d', float_value))[0]
        else:
            return struct.unpack('I', struct.pack('f', float_value))[0]