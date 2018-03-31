from flask import *
from indexer import indexing, query_processing, build_index, dict_optimization, doc2words
from indexer.search_engine import *
app = Flask(__name__)


def op(fp):
    with open(fp, 'r', encoding='cp1251') as fl:
        return fl.read()


def query_search(req):
    query_string = query_stack.process(req)
    results = query_string.get_query_urls(len(url_list))

    for doc_url_idx in results:
        yield doc_url_idx


def generate_index(ind):
    print('Index Gen...')
    files = [(int(i), {'url': url, 'text': op('root/' + str(i) + '.txt')}) for i, url in zip(ind, ind.values())]
    indexing.run('simple9', files)
    build_index.run()
    dict_optimization.run()


#------------------------------------------#


@app.route('/search')
def search():
    req = request.args.get('req')
    if req is None:
        abort(418)
    res = []
    for url in query_search(doc2words.normal(req).replace(' ', ' & ')):
        if len(res) >= 20:
            break
        try:
            snippet = indexing.get_snippet(url, doc2words.normal(req))
            res.append({'url': url_for('go', url=url_list[url]), 'head': snippet[0], 'body': snippet[1]})
        except:
            pass
    return res

def SpiderRun():
    from spider.spider import CrawlerRunner
    c = CrawlerRunner()
    try:
        with open('last_ind.tmp') as f:
            last_ind = f.read()
        if last_ind != max(c.crawler.index, key=lambda x: int(x)):
            generate_index(c.crawler.index)
    except FileNotFoundError:
        generate_index(c.crawler.index)
        with open('last_ind.tmp', 'w') as f:
            f.write('0')
if __name__ == '__main__':
    #SpiderRun()
    path = './temp_idx/'
    with open(path + 'encoding.ini', 'r') as f_config:
        encoding = f_config.readline()
    index = SearchIndex(path + 'entire_index', path + 'terms_dict', encoding)
    with open(path + 'url_list', 'r') as urls_filename:
        url_list = urls_filename.readlines()
        url_list = [url[:-1] for url in url_list]
    query_stack = QueryProcessor(index)
    #app.run(port=8121)
