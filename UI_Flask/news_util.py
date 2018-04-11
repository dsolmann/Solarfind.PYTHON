import json, sys
ar = open("news_data/news.json")
a = json.load(ar)
hdr = input("Input Header: ")
print("Input Body: ")
bdy=""
while True:
    bdy+=sys.stdin.read()
    if "$" in list(bdy):
        print("OK")
        bdy = bdy[:-2]
        break
print("Your text is: ",bdy)
a[hdr]=bdy
ar.close()
ar = open("news_data/news.json", 'w')
json.dump(a, ar)