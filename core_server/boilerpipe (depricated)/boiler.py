import os, html2text
h = html2text.HTML2Text()
h.ignore_links = True
def ReadADoc(name):
    f = open(name, "rb")
    try:
       a = f.read().decode('utf-8')
    except UnicodeDecodeError:
        try:
           a = f.read().decode('cp-1251')
        except:
            try:
               a = f.read().decode('utf-8', errors="replace")
            except:
                a = f.read().decode('utf-8', errors="ignore")
    f.close()
    return a
def WriteADoc(name, data):
    f = open(name, 'wb')
    f.write(data.encode('utf-8'))
    f.close()
def handle(out_dir, index):
    doch = ReadADoc("/Alpha_1/html/"+str(index))
    a = h.handle(doch)
    WriteADoc("/Alpha_1/root/"+str(index)+'.txt', a)