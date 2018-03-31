import os

from .docreader import *
import sys
import functools


def read_term_dict_partitions(dict_filenames):
    dict_partition_files = [open(filename, 'rb') for filename in dict_filenames]
    dict_partitions = []
    for dict_part_file in dict_partition_files:
        partition_len = struct.unpack("Q", dict_part_file.read(8))[0]
        partition_dct = {}
        for foo in range(partition_len):
            key = struct.unpack("q", dict_part_file.read(8))[0]
            offset = struct.unpack("I", dict_part_file.read(4))[0]
            seq_len = struct.unpack("I", dict_part_file.read(4))[0]
            partition_dct[key] = (offset, seq_len)
        dict_partitions.append(partition_dct)
    for dict_part_file in dict_partition_files:
        dict_part_file.close()
    return dict_partitions


def write_entire_index(index_filenames, result_index_filename, terms_keys, dict_partitions):
    terms_dict = {}
    index_files = [open(f, 'rb') for f in index_filenames]
    with open(result_index_filename, 'wb') as entire_index_file:
        term_offset = 0
        for key in terms_keys:
            term_length = 0
            for partition_idx, partition in enumerate(dict_partitions):
                if key in partition:
                    offset, n_bytes = partition[key]
                    index_files[partition_idx].seek(offset)
                    encoded_seq = index_files[partition_idx].read(n_bytes)
                    entire_index_file.write(encoded_seq)
                    term_length += len(encoded_seq)

            terms_dict[key] = (term_offset, term_length)
            term_offset += term_length

    for f in index_files:
        f.close()
    return terms_dict


def write_entire_term_dict(dict_filename, all_terms):
    with open(dict_filename, 'wb') as entire_dict_file:
        entire_dict_file.write(struct.pack("Q", len(all_terms)))
        for key, (offset, seq_len) in all_terms.items():
            entire_dict_file.write(struct.pack("qII", key, offset, seq_len))


def run():
    input_files = []
    path = './temp_idx/'
    for input_filename in os.listdir(path):
        if input_filename.endswith(".dct"):
            input_files += [path + input_filename]
        else:
            continue

    # input_files = parse_command_line().files
    entire_index_filename = './temp_idx/entire_index'
    entire_dict_filename = './temp_idx/terms_dict'

    if len(input_files) == 1:
        dict_filename = input_files[0]
        index_filename = input_files[0][:-4] + '.idx'
        # sys.stderr.write('input_files:\n')
        # sys.stderr.writelines(input_files)
        # sys.stderr.write('dict_filename = {0}\n'.format(dict_filename))
        # sys.stderr.write('index_filename = {0}\n'.format(index_filename))
        if os.path.isfile(entire_dict_filename):
            os.remove(entire_dict_filename)
        if os.path.isfile(entire_index_filename):
            os.remove(entire_index_filename)
        os.rename(dict_filename, entire_dict_filename)
        os.rename(index_filename, entire_index_filename)
        sys.stderr.write("Index is built successfully (quick)\n")
        return

    term_dict_filenames = input_files
    index_filenames = [filename[:-4] + '.idx' for filename in input_files]

    dict_partitions = read_term_dict_partitions(term_dict_filenames)
    all_terms_keys = functools.reduce(lambda x, y: x | y, [set(partition.keys()) for partition in dict_partitions])
    all_terms = write_entire_index(index_filenames, entire_index_filename, all_terms_keys, dict_partitions)
    write_entire_term_dict(entire_dict_filename, all_terms=all_terms)

    for f in term_dict_filenames + index_filenames:
        os.remove(f)
    sys.stderr.write("Index is built successfully\n")
