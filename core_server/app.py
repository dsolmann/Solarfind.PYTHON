# -*- coding: utf-8 -*-

from indexer import indexing, build_index, dict_optimization, doc2words
from indexer.search_engine import *
from flask import *
import json


app = Flask(__name__)


def op(fp):
    with open(fp, encoding='utf-8') as fl:
        return fl.read()


def generate_index(ind):
    print('Index Gen...')
    indexes = sorted(ind.keys(), key=lambda x: int(x))
    files = [(int(i), {'url': ind[i], 'text': op('root/' + str(i) + '.txt')}) for i in indexes]
    indexing.run('simple9', files)
    build_index.run()
    dict_optimization.run()


@app.route('/search')
def search():
    return json.dumps(s.search(request.args.get('s')))


# ------------------------------------------ #


class Searcher:
    def __init__(self):
        path = '/Alpha_1/core_server/temp_idx/'
        with open(path + 'encoding.ini', 'r') as f_config:
            encoding = f_config.readline()
        index = SearchIndex(path + 'entire_index', path + 'terms_dict', encoding)
        with open(path + 'url_list', 'r') as urls_filename:
            url_list = urls_filename.readlines()
            self.url_list = [url[:-1] for url in url_list]
        self.query_stack = QueryProcessor(index)

    def _search(self, req):
        query_string = self.query_stack.process(req)
        results = query_string.get_query_urls(len(self.url_list))

        for doc_url_idx in results:
            yield doc_url_idx

    def search(self, req):
        if req is None:
            return
        res = []
        for url in self._search(doc2words.normal(req).replace(' ', ' & ')):
            if len(res) >= 20:
                break
            snippet = indexing.get_snippet(url, doc2words.normal(req))
            res.append([snippet[0], self.url_list[url], snippet[1]])
        return res


if __name__ == '__main__':
    # from spider.spider import CrawlerRunner
    # c = CrawlerRunner()
    # input()

    # with open('index.json') as f:
    #     generate_index(json.load(f))
    s = Searcher()
    app.run('127.0.0.1', port=8121)
