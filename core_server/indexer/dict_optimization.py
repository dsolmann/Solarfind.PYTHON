import struct
from collections import Counter

BUCKETS_COUNT = 4096


def optimize_term_dict(term_dict, filename, buckets_count):
    hashed_keys = [(key, key % buckets_count) for key in term_dict.keys()]
    keys_count = Counter([hk[1] for hk in hashed_keys])
    buckets_size = \
        [bucket_idx for key, bucket_idx in sorted(keys_count.items(), key=lambda x: x[0])]
    with open(filename, 'wb') as dict_file:
        dict_file.write(struct.pack('I', buckets_count))
        for size_of_bucket in buckets_size:
            dict_file.write(struct.pack('I', size_of_bucket))
        for current_bucket_idx in range(buckets_count):
            keys_in_bins = \
                sorted([key for (key, bucket_idx) in hashed_keys if bucket_idx == current_bucket_idx])
            for key in keys_in_bins:
                offset, seq_len = term_dict[key]
                dict_file.write(struct.pack('q2I', key, offset, seq_len))


def run():
    entire_dict_filename = './temp_idx/terms_dict'
    with open(entire_dict_filename, 'rb') as term_dict_file:
        terms_count = struct.unpack("Q", term_dict_file.read(8))[0]
        terms_seq = list(struct.unpack("qII" * terms_count, term_dict_file.read((8 + 4 + 4) * terms_count)))
        entire_dict = {
            terms_seq[i]: (terms_seq[i + 1], terms_seq[i + 2])
            for i in range(0, 3 * terms_count, 3)
        }
    optimize_term_dict(entire_dict, entire_dict_filename, BUCKETS_COUNT)
