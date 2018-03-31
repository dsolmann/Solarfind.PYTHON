
import argparse
from . import document_pb2
import struct
import gzip


class DocumentStreamReader:
    def __init__(self, paths):
        self.paths = paths

    @staticmethod
    def open_single(path):
        return gzip.open(path, 'rb') if path.endswith('.gz') else open(path, 'rb')

    def __iter__(self):
        for path in self.paths:
            with self.open_single(path.rstrip()) as stream:
                while True:
                    sb = stream.read(4)
                    if sb == b'':
                        break

                    size = struct.unpack('i', sb)[0]
                    msg = stream.read(size)
                    doc = document_pb2.document()
                    doc.ParseFromString(msg)
                    yield doc


def parse_command_line():
    parser = argparse.ArgumentParser(description='compressed documents reader')
    parser.add_argument('files', nargs='+', help='Input files (.gz or plain) to process')
    return parser.parse_args()


if __name__ == '__main__':
    reader = DocumentStreamReader(parse_command_line().files)
    for d in reader:
        print("%s\t%d bytes" % (d.url, len(d.text)))
