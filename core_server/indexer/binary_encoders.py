import struct
import numpy as np
from functools import reduce


class Simple9Encoder:
    def __init__(self):
        self.__bitcounts_of_numbers = [28, 14, 9, 7, 5, 4, 3, 2, 1]
        self.__numbers_in_package = [28 // cnt for cnt in self.__bitcounts_of_numbers]

    @staticmethod
    def __get_bitcount_for_number(num):
        for count in range(1, 29):
            if num >> count == 0:
                return count

    def __make_s9_package(self, nums_of_package, packing_type_idx):
        bits_per_number = self.__bitcounts_of_numbers[packing_type_idx]
        rest_bits = 28 % bits_per_number
        package = packing_type_idx << rest_bits
        if type(nums_of_package) is list:
            for current_number in nums_of_package:
                package = (package << bits_per_number) | current_number
            return package
        else:
            return (package << bits_per_number) | nums_of_package

    def encode(self, num_sequence):
        if not hasattr(num_sequence, '__len__'):
            num_sequence = [num_sequence]

        numbers_len = list(map(lambda x: self.__get_bitcount_for_number(x), num_sequence))
        n_nums_encoded, simple9_packs = 0, []
        while n_nums_encoded < len(num_sequence):
            for packing_type_idx in reversed(range(8)):
                bits_per_number = self.__bitcounts_of_numbers[packing_type_idx]
                nums_per_package = self.__numbers_in_package[packing_type_idx]
                rest_bits = 28 % bits_per_number
                if n_nums_encoded + nums_per_package > len(num_sequence):
                    continue
                pack_lens = numbers_len[n_nums_encoded: n_nums_encoded + nums_per_package]
                if sum(pack_lens) + rest_bits <= 28 and max(pack_lens) <= bits_per_number:
                    current_pack_numbers = num_sequence[n_nums_encoded: n_nums_encoded + nums_per_package]
                    simple9_packs.append(self.__make_s9_package(current_pack_numbers, packing_type_idx))
                    n_nums_encoded += nums_per_package
                    break

        byte_blocks = [struct.unpack("4B", struct.pack("I", pack)) for pack in simple9_packs]
        byte_sequence = reduce(lambda x, y: x + y, byte_blocks)
        return bytearray(byte_sequence)

    def __decode_s9_package(self, package):
        packing_type_idx = package >> 28
        mask = 2 ** self.__bitcounts_of_numbers[packing_type_idx] - 1
        result_sequence = []
        for i in range(self.__numbers_in_package[packing_type_idx]):
            result_sequence += [package & mask]
            package >>= self.__bitcounts_of_numbers[packing_type_idx]
        return list(reversed(result_sequence))

    def decode(self, encoded_numbers):
        encoded_numbers = [struct.unpack("I", encoded_numbers[i: i + 4])[0] for i in range(0, len(encoded_numbers), 4)]
        numbers = [self.__decode_s9_package(n) for n in encoded_numbers]
        return reduce(lambda x, y: x + y, numbers)


class VarbyteEncoder:

    @staticmethod
    def __encode_number(number):
        result_bytes = []
        while True:
            result_bytes.append(number & 0x7f)
            number >>= 7
            if number == 0:
                break
        result_bytes[0] |= 0x80
        result_bytes.reverse()
        return result_bytes

    def encode(self, num_sequence):
        if not hasattr(num_sequence, '__len__'):
            num_sequence = [num_sequence]

        bytes_of_nums = map(self.__encode_number, num_sequence)

        result_bytes = []
        for seq in bytes_of_nums:
            result_bytes += seq
        return bytearray(result_bytes)

    @staticmethod
    def decode(b):
        numbers = []

        current_number = 0
        for byte in b:
            current_number <<= 7
            current_number += byte & 0x7f
            if byte & 0x80 > 0:
                numbers.append(current_number)
                current_number = 0
        return numbers


def encode_sequence(seq_to_encode, encoding='varbyte'):
    deltas = [x - y for x, y in zip(seq_to_encode[1:], seq_to_encode)]
    if encoding == 'varbyte':
        return VarbyteEncoder().encode(deltas)
    elif encoding == 'simple9':
        return Simple9Encoder().encode(deltas)


def decode_sequence(seq_to_decode, encoding='varbyte'):
    encoder = None
    if encoding == 'varbyte':
        encoder = VarbyteEncoder()
    elif encoding == 'simple9':
        encoder = Simple9Encoder()
    dec_deltas = encoder.decode(seq_to_decode)
    return np.cumsum(dec_deltas)


def test():
    foo = [2]
    bar = np.array(2)
    print(hasattr(foo, '__len__'))
    print(hasattr(bar, '__len__'))

    method = Simple9Encoder()

    nums = [0, 4, 30, 200, 40000, 3000000]

    print("numbers:", nums)
    numbers_encoded = method.encode(nums)
    numbers_decoded = method.decode(numbers_encoded)

    print("decoded:", numbers_decoded)

    method = 'varbyte'
    if len(numbers_decoded) > 1:
        s1 = encode_sequence(nums, encoding=method)
        print("foo:", decode_sequence(s1, encoding=method))
