from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import urllib.parse
from bs4 import BeautifulSoup
import socket
from threading import Thread, Lock
import time
from collections import defaultdict
import json
import re
from boilerpipe import boiler


class Crawler(Thread):
    init_url = 'https://mail.ru/'
    anchor = "*"
    anchor_end = ".mail.ru"
    restricted_hosts = ["m.mail.ru"]

    save_freq = 100

    output_dir = 'html'
    debug = True

    delay = 0.05
    max_depth = 32
    timeout = 2.0
    max_attempts = 10
    max_pages = 3000

    repeat_start_time = 60
    repeat_max_time = 60*60
    delta = 2
    id = 0
    index = {}
    visited = set()

    def __init__(self):
        self.repeat_attempt = defaultdict(lambda: [self.repeat_start_time / self.delta, 0])

        self.bag = [self.init_url]
        self.disallow = set()

        self.working = True
        super().__init__(target=self.run)
        # self.get_disallow()
        self.lock = Lock()
        self.start()
        self.go(self.max_depth)
        self.working = False

        self.max_thread = 8

    def run(self):
        while self.working or len(self.repeat_attempt):
            for url in self.repeat_attempt.copy():
                with self.lock:
                    if self.repeat_attempt[url][0] >= self.repeat_max_time:
                        del self.repeat_attempt[url]
                    elif time.time() - self.repeat_attempt[url][1] >= self.repeat_attempt[url][0]:
                        self.bag.append(url)
            time.sleep(self.repeat_start_time // 2)

    def get_url(self, url, href):
        combined_url = urllib.parse.urljoin(url, href)
        s = urllib.parse.urlparse(combined_url)
        if s.netloc in self.restricted_hosts:
            return
        if s.netloc == self.anchor or s.netloc.endswith(self.anchor_end) or self.anchor == '*':
            return combined_url

    def get_disallow(self):
        if not self.get_url(self.init_url, 'robots.txt'):
            return
        try:
            req = urlopen(Request(self.get_url(self.init_url, 'robots.txt')), timeout=self.timeout)
            robots = req.read().decode().split('\n')
            for rule in robots:
                if 'Disallow:' in rule:
                    disallow = rule.split(': ')[1]
                    self.disallow.add(self.get_url(self.init_url, disallow))
        except (HTTPError, URLError, socket.timeout, IndexError):
            pass

    def fetch(self, url):
        for _ in range(self.max_attempts):
            try:
                req = urlopen(Request(url), timeout=self.timeout)
                html = req.read()
                doc_structure = BeautifulSoup(html, "html.parser")
                children_urls = []
                for link in doc_structure.findAll('a'):
                    try:
                        static_url = self.get_url(url, link['href'])
                        if static_url:
                            children_urls.append(static_url)
                    except KeyError:
                        pass
                break
            except HTTPError as e:
                if e.code == '404' or e.code == '500':
                    self.repeat_attempt[url][0] *= self.delta
                    self.repeat_attempt[url][1] = time.time()
                return False, '', list()
            except socket.timeout as e:
                self.repeat_attempt[url][0] *= self.delta
                self.repeat_attempt[url][1] = time.time()
                print(str(e))
                return False, '', list()
            except (URLError, UnicodeEncodeError) as e:
                print(e)
                return False, '', list()
        else:
            return False, '', list()
        return True, html, children_urls

    def go(self, current_depth):
        if current_depth <= 0:
            return self.index
        for i, url in enumerate(self.bag.copy()):
            if url in self.visited and len(self.bag) != 1:
                continue
            for dis in self.disallow:
                if len(re.findall(dis, url)):
                    break
            else:
                self.bag.pop(i)
                status, html, children_urls = self.fetch(url)
                if not status:
                    continue
                self.bag += children_urls
                self.index[self.id] = url
                self.visited.add(url)
                with open("{0}/{1}".format(self.output_dir, self.id), "wb") as f:
                    f.write(html)

                boiler.handle(self.output_dir, str(self.id))

                if self.debug:
                    print("{0}\t{1}".format(self.id, url))
                self.id += 1
                if not self.id % self.save_freq and self.id:
                    with open("index.json", "w") as ind:
                        json.dump(self.index, ind, indent=2)
                    with open('last_ind.tmp', 'w') as last:
                        last.write(str(self.id - 1))
                    # generate_index(self.index)
                time.sleep(self.delay)
                self.max_pages -= 1
                if self.max_pages <= 0:
                    return self.index
        if len(self.bag) > 0:
            self.go(current_depth - 1)
        return self.index


class CrawlerRunner(Thread):

    def __init__(self):
        super().__init__(target=self.run)
        self.crawler = Crawler
        try:
            with open('index.json') as f:
                index = json.load(f)
            ids = max(index, key=lambda x: int(x))
            self.crawler.id = int(ids)
            self.crawler.init_url = index[ids]
            self.crawler.index = index
            self.crawler.visited = set(index.values())
        except FileNotFoundError:
            pass
        self.start()

    def run(self):
        print('Запуск паука...')
        self.crawler()
