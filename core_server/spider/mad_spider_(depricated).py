from bs4 import BeautifulSoup
from time import sleep
import urllib2
import urlparse


MAX_DEPTH = 32
DELAY = 0.05
LARGE_DELAY = 1.0
MAX_ATTEMTS = 10
PAGES_COUNT_QUOTA = 3000
INIT_URL = "http://lenta.ru"
ANCHOR = "lenta.ru"
ANCHOR_END = ".lenta.ru"
RESTRICTED_HOSTS = ["m.lenta.ru"]
OUTPUT_DIR = "data"


def fetch_url_impl(url):
    is_ok = True
    html = None
    for attempt in xrange(MAX_ATTEMTS):
        try:
            req = urllib2.urlopen(url)
            html = req.read()
            break
        except urllib2.HTTPError as he:
            if he.code == 403 or he.code == 404:
                is_ok = False
                return is_ok, html, list()
            else:
                print("HTTPError {0} occured!".format(he.code))
                sleep(LARGE_DELAY)
        except urllib2.URLError as ue:
            print("URLError {0} occured!".format(ue))
            is_ok = False
            return is_ok, html, list()
    if html is None:
        print("General spider failure")
        exit(1)
    doc_structure = BeautifulSoup(html, "html.parser")
    children_urls = list()
    for link in doc_structure.findAll('a'):
        try:
            href = link["href"]
            combined_url = urlparse.urljoin(url, href)
            steine = urlparse.urlparse(combined_url)
            if steine.netloc in RESTRICTED_HOSTS:
                continue
            if steine.netloc == ANCHOR or steine.netloc.endswith(ANCHOR_END):
                children_urls.append(combined_url)
        except KeyError:
            pass
    return is_ok, html, children_urls


def fetch_urls(urls_bag,
               index=None,
               visited=None,
               current_id=0,
               depth_quota=MAX_DEPTH,
               count_quota=PAGES_COUNT_QUOTA):
    if index is None:
        index = dict()
    if visited is None:
        visited = set()
    new_bag = []
    for url in urls_bag:
        if url in visited:
            continue
        is_ok, html, children_urls = fetch_url_impl(url)
        if is_ok:
            new_bag += children_urls
            index[current_id] = url
            visited.add(url)
            with open("{0}/{1}.html".format(OUTPUT_DIR, current_id), "w") as filep:
                filep.write(html)
            # print("Document '{0}' is downloaded, ID={1}".format(url, current_id))
            print("{0}\t{1}".format(current_id, url))
            current_id += 1
        sleep(DELAY)
        count_quota -= 1
        if count_quota == 0:
            return index
    if len(new_bag) > 0:
        fetch_urls(new_bag, index, visited, current_id, depth_quota-1, count_quota)
    return index


index = fetch_urls([INIT_URL])
with open("index.txt", "w") as indexf:
    for id, url in index.iteritems():
        indexf.write("{0}\t{1}\n".format(id, url))