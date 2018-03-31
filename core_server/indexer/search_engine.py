# -*- coding: utf-8 -*

import sys
import struct

import numpy as np

from .binary_encoders import decode_sequence
from .query_processing import *
from bisect import bisect_left
import mmh3


class TermDictionary:
    def __init__(self, dict_filename):
        self.file = open(dict_filename, 'rb')
        self.buckets_count = struct.unpack("I", self.file.read(4))[0]
        self.buckets_size = list(struct.unpack("{0}I".format(self.buckets_count),
                                               self.file.read(4 * self.buckets_count)))
        self.buckets = []
        for bucket_idx in range(self.buckets_count):
            current_bucket = np.asarray(struct.unpack(
                'q2I' * self.buckets_size[bucket_idx],
                self.file.read((8 + 4 + 4) * self.buckets_size[bucket_idx])
            )).reshape(-1, 3)
            self.buckets.append(current_bucket)
        self.file.close()

    def find(self, item):
        key = mmh3.hash64(item)[0]
        bucket_idx = key % self.buckets_count
        target_bucket = self.buckets[bucket_idx]
        term_idx = TermDictionary.__binary_search(target_bucket[:, 0], key)
        offset, n_bytes = target_bucket[term_idx, 1], target_bucket[term_idx, 2]
        return offset, n_bytes

    # def find(self, item):
    #     bucket_idx = hash(item) % self.buckets_count
    #     offset = sum([self.buckets_size[i] * (8 + 4 + 4) for i in range(bucket_idx)]) + 4 + 4 * self.buckets_count
    #     self.file.seek(offset)
    #
    #     target_bucket = np.asarray(struct.unpack(
    #         'q2I' * self.buckets_size[bucket_idx],
    #         self.file.read((8 + 4 + 4) * self.buckets_size[bucket_idx])
    #     )).reshape(-1, 3)
    #
    #     idx = TermDictionary.__binary_search(target_bucket[:, 0], hash(item))
    #     offset, n_bytes = target_bucket[idx, 1], target_bucket[idx, 2]
    #     return offset, n_bytes

    # def __del__(self):
    #     self.file.close()

    @staticmethod
    def __binary_search(x, elem):
        i = bisect_left(x, elem)
        if i != len(x) and x[i] == elem:
            return i
        raise ValueError('Error while searching in term dictionary')


class SearchIndex:
    def __init__(self, file_name_index, file_name_terms, encoding):
        self.file = open(file_name_index, 'rb')
        self.terms = TermDictionary(file_name_terms)
        self.encoding_method = encoding

    def get_related_docs(self, term):
        try:
            offset, bytes_to_read = self.terms.find(term)
        except ValueError:
            return []
        self.file.seek(offset)
        bytes_seq = self.file.read(bytes_to_read)
        return decode_sequence(bytearray(bytes_seq), encoding=self.encoding_method)

    def __del__(self):
        self.file.close()


def run():
    path = './temp_idx/'
    with open(path + 'encoding.ini', 'r') as f_config:
        encoding = f_config.readline()
    index = SearchIndex(path + 'entire_index', path + 'terms_dict', encoding)
    with open(path + 'url_list', 'r') as urls_filename:
        url_list = urls_filename.readlines()
        url_list = [url[:-1] for url in url_list]

    query_stack = QueryProcessor(index)
    queries = sys.stdin.readlines()
    for query_string in queries:
        print(query_string[:-1])
        query_string = query_stack.process(query_string)
        results = query_string.get_query_urls(len(url_list))

        print(len(results))
        for doc_url_idx in results:
            print(url_list[doc_url_idx])
