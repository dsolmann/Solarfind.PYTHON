import json
import sys

news_path = 'apps/news/data/news.json'

with open(news_path) as ar:
    a = json.load(ar)
    hdr = input("Input Header: ")
    print("Input Body: ")
    bdy = ""
    while True:
        bdy += sys.stdin.read()
        if "$" in list(bdy):
            print("OK")
            bdy = bdy[:-2]
            break
    print("Your text is: ", bdy)
    a[hdr] = bdy

with open(news_path, 'w') as r:
    json.dump(a, ar)
