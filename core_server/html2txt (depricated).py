import os
import html2text

h = html2text.HTML2Text()
h.ignore_links = True
h.ignore_images = True


def handle(input_dir, out_dir, index):

    with open(os.path.join(input_dir, index), "rb") as f:
        try:
            data = f.read().decode('utf-8')
        except UnicodeDecodeError:
            try:
                data = f.read().decode('cp-1251')
            except:
                data = ''

    with open(os.path.join(out_dir, index + '.txt'), 'wb') as f:
        try:
            f.write(h.handle(data).encode())
        except:
            f.write(b'')
