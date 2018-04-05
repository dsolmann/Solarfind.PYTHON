import os


def handle(inp, out, index):
    os.system("java -jar boilerpipe/boilerpipe.jar {0} > {1}".format(os.path.join(inp, index),
                                                                     os.path.join(out, index + '.txt')))
