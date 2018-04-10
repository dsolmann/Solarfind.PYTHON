from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import urllib.parse
from bs4 import BeautifulSoup
import socket
from threading import Thread, RLock
import time
import json
import re
from boilerpipe.boiler import BoilerWithShingle
from tqdm import tqdm


class Crawler(Thread):
    save_freq = 5

    debug = True

    delay = 0.05
    max_depth = 32
    timeout = 2.0
    max_attempts = 10

    repeat_start_time = 60
    repeat_max_time = 60*60
    delta = 2

    def __init__(self, runner, init_url, anchor='*'):
        super().__init__(target=self.run)

        self.runner = runner
        self.init_url = init_url
        self.anchor = anchor

        self.bag = [self.init_url]
        self.disallow = set()
        self.running = True

    def run(self):
        try:
            self.go(self.max_depth)
        except Exception as ex:
            if str(ex) != 'Stop':
                self.runner.remove(self)
        else:
            self.runner.remove(self)

    def stop(self):
        self.running = False

    def get_url(self, url, href):
        combined_url = urllib.parse.urljoin(url, href).split('?')[0].split('#')[0]
        s = urllib.parse.urlparse(combined_url)
        if s.netloc in self.runner.restricted_hosts:
            return
        if s.netloc == self.anchor or s.netloc.endswith(urllib.parse.urlparse(self.init_url).netloc):
            return combined_url
        if self.anchor == '*':
            self.runner.lock.acquire()
            self.runner.add(Crawler(self.runner, combined_url))
            self.runner.lock.release()

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
            except (HTTPError, socket.timeout, URLError, UnicodeEncodeError) as e:
                self.runner.pbar.write(str(e))
                return False, '', list()
        else:
            return False, '', list()
        return True, html, children_urls

    def go(self, current_depth):
        if current_depth <= 0:
            return self.runner.index
        for i, url in enumerate(self.bag.copy()):
            if not self.running:
                raise Exception('Stop')
            if url in self.runner.visited and len(self.bag) != 1:
                continue
            for dis in self.disallow:
                if re.findall(dis, url):
                    break
            else:
                self.bag.pop(i)
                status, html, children_urls = self.fetch(url)
                if not status:
                    continue
                self.bag += children_urls

                self.runner.lock.acquire()
                try:
                    ids = str(self.runner.id)
                    self.runner.index[self.runner.id] = url
                    self.runner.visited.add(url)
                    self.runner.id += 1

                    if not self.runner.id % self.save_freq and self.runner.id:
                        with open("index.json", "w") as ind:
                            json.dump(self.runner.index, ind, indent=2)
                        with open('last_ind.tmp', 'w') as last:
                            last.write(str(self.runner.id - 1))
                except Exception as ex:
                    self.runner.pbar.write(ex)
                self.runner.lock.release()

                with open("{0}/{1}".format(self.runner.output_dir, ids), "wb") as f:
                    f.write(html)

                if self.debug:
                    self.runner.pbar.write("{0}\t{1}".format(ids, url))

                code = self.runner.boiler.handle(self.runner.output_dir, self.runner.txt_dir, ids)
                if not code:
                    try:
                        self.runner.index.pop(ids)
                    except IndexError as e:
                        self.runner.pbar.write(str(e))
                else:
                    self.runner.max_pages -= 1
                    self.runner.pbar.update(1)

                if self.runner.max_pages <= 0:
                    self.runner.stop()

                time.sleep(self.delay)
        if self.bag:
            self.go(current_depth - 1)
        return self.runner.index


class CrawlerRunner:

    max_crawlers = 8

    restricted_hosts = []

    output_dir = 'html/'
    txt_dir = 'root/'

    max_pages = 9000

    def __init__(self):
        self.visited = set()
        self.index = {}
        self.id = 0
        self.lock = RLock()

        self.boiler = BoilerWithShingle()
        self.pbar = tqdm(total=self.max_pages)
        self.query = []

        self.active_crawlers = [Crawler(self, 'https://habrahabr.ru/')]

        for crawler in self.active_crawlers:
            crawler.start()

        self.running = True

    def add(self, crawler):
        if len(self.active_crawlers) >= self.max_crawlers:
            self.query.append(crawler)
        else:
            self.active_crawlers.append(crawler)
            crawler.start()

    def remove(self, crawler):
        self.active_crawlers.remove(crawler)
        new_crawler = self.query.pop(0)
        self.active_crawlers.append(new_crawler)
        new_crawler.start()

    def stop(self):
        self.running = False
        for crawler in self.active_crawlers:
            crawler.stop()
        print('Spider has stopped')
        self.pbar.close()

    def find_duplicates(self):
        self.boiler.find(self.index)
