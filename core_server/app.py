# -*- coding: utf-8 -*-

from indexer import indexing, build_index, dict_optimization, doc2words
from indexer.search_engine import *
from flask import *
import json
import random
import time

app = Flask(__name__)


def op(fp):
    try:
        with open(fp, encoding='utf-8') as fl:
            return fl.read()
    except FileNotFoundError:
        return ''


def generate_index(ind):
    print('Index Gen...')
    indexes = sorted(ind.keys(), key=lambda x: int(x))
    files = []
    for i in indexes:
        files.append((int(i), {'url': ind[i], 'text': op('root/' + str(i) + '.txt')}))
    indexing.run('simple9', files)
    build_index.run()
    dict_optimization.run()


@app.route('/search')
def search():
    return json.dumps(s.search(request.args.get('s'), int(request.args.get('p', default=1)) - 1))


@app.route('/example')
def get_example():
    if doc2words.dct.values():
        return random.choice(list(doc2words.dct.values()))
    return 'Попробуйте найти что-нибудь...'


# ------------------------------------------ #


class Searcher:
    def __init__(self):
        path = 'temp_idx/'
        with open(path + 'encoding.ini', 'r') as f_config:
            encoding = f_config.readline()
        ind = SearchIndex(path + 'entire_index', path + 'terms_dict', encoding)
        with open('index.json', 'r') as urls:
            self.index = json.load(urls)
        self.query_stack = QueryProcessor(ind)

    def _search(self, req):
        query_string = self.query_stack.process(req)
        return query_string.get_query_urls(len(self.index))

    def search(self, req, p=0):
        if not req:
            return json.dumps({'time': 0.0, 'total': 0, 'data': []})
        data = []
        req = doc2words.normal(req)
        t = time.time()
        indexes = self._search(req.replace(' ', ' & '))
        t = time.time() - t
        for ind in indexes[p*20:(p+1)*20]:
            try:
                snippet = indexing.get_snippet(ind, req)
                data.append([snippet[0], self.index[str(ind)], snippet[1], snippet[2]])
            except AttributeError:
                pass
        return json.dumps({'time': t, 'total': len(indexes), 'data': data})


if __name__ == '__main__':
    # from spider.spider import CrawlerRunner
    # c = CrawlerRunner()

    # while c.running:
    #     time.sleep(5)

    # with open('index.json') as f:
    #     index = json.load(f)
    # with open('index_back.json', 'w') as f:
    #     json.dump(index, f)
    # c.find_duplicates()

    # from boilerpipe.boiler import BoilerWithShingle
    # b = BoilerWithShingle()
    # for ind in index:
    #     b.add(ind)
    # b.find(index)

    # generate_index(index)
    s = Searcher()
    app.run('127.0.0.1', port=8121)
