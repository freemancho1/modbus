import struct
from threading import Lock


class DataBank:

    bits_lock = Lock()
    bits = [False] * 0x10000
    words_lock = Lock()
    words = [0] * 0x10000

    @classmethod
    def get_bits(cls, address, number=1):
        with cls.bits_lock:
            if (address >= 0) and (address + number <= len(cls.bits)):
                return cls.bits[address:address+number]
            else:
                return None

    @classmethod
    def set_bits(cls, address, bit_list):
        result = None
        bit_list = [bool(b) for b in bit_list]
        with cls.bits_lock:
            if (address >= 0) and (address+len(bit_list) <= len(cls.bits)):
                cls.bits[address:address+len(bit_list)] = bit_list
                result = True
        return result

    @classmethod
    def get_words(cls, address, number=1):
        with cls.words_lock:
            if (address >= 0) and (address+number <= len(cls.words)):
                return cls.words[address:address+number]
            else:
                return None

    @classmethod
    def set_words(cls, address, word_list):
        result = None
        word_list = [int(w) & 0xffff for w in word_list]
        with cls.words_lock:
            if (address >= 0) and (address+len(word_list) <= len(cls.words)):
                cls.words[address:address+len(word_list)] = word_list
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