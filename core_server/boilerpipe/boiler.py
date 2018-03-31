import os, html2text
h = html2text.HTML2Text()
h.ignore_links = True
def ReadADoc(name):
    f = open(name, "rb")
    a = f.read().decode('utf-8')
    f.close()
    return a
def WriteADoc(name, data):
    f = open(name, 'wb')
    f.write(data.encode('utf-8'))
    f.close()
def handle(out_dir, index):
    doch = ReadADoc("html/"+str(index))
    a = h.handle(doch)
    WriteADoc("root/"+str(index)+'.txt', a)