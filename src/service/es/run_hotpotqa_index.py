from multiprocessing import Pool
import json
import os, time, random
from elasticsearch import Elasticsearch
import json
from flask import Flask
from flask import request
from flask_cors import CORS, cross_origin
import re


app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


WIKIPEDIA_INDEX_NAME='wikipedia'

core_title_matcher = re.compile('([^()]+[^\s()])(?:\s*\(.+\))?')
core_title_filter = lambda x: core_title_matcher.match(x).group(1) if core_title_matcher.match(x) else x

class ElasticSearch:
    def __init__(self):
        self.client = Elasticsearch(timeout=300,hosts="http://127.0.0.1:9200")
    
    def _extract_one(self, item, lazy=False):
        res = {k: item['_source'][k] for k in ['id', 'url', 'title', 'text', 'title_unescape']}
        # res['_score'] = item['_score']
        # res['data_object'] = item['_source']['original_json'] if lazy else json.loads(item['_source']['original_json'])
        return res

    def _extract_one(self, item, lazy=False):
        res = {k: item['_source'][k] for k in ['id', 'url', 'title', 'text', 'title_unescape']}
        res['_score'] = item['_score']
        res['data_object'] = item['_source']['original_json'] if lazy else json.loads(item['_source']['original_json'])

        return res
    def rerank_with_query(self, query, results):
        def score_boost(item, query):
            score = item['_score']
            core_title = core_title_filter(item['title_unescape'])
            if query.startswith('The ') or query.startswith('the '):
                query1 = query[4:]
            else:
                query1 = query
            if query == item['title_unescape'] or query1 == item['title_unescape']:
                score *= 1.5
            elif query.lower() == item['title_unescape'].lower() or query1.lower() == item['title_unescape'].lower():
                score *= 1.2
            elif item['title'].lower() in query:
                score *= 1.1
            elif query == core_title or query1 == core_title:
                score *= 1.2
            elif query.lower() == core_title.lower() or query1.lower() == core_title.lower():
                score *= 1.1
            elif core_title.lower() in query.lower():
                score *= 1.05

            item['_score'] = score
            return item

        return list(sorted([score_boost(item, query) for item in results], key=lambda item: -item['_score']))

    def single_text_query(self, query, topn=10, lazy=False, rerank_topn=50):
        constructed_query = {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^1.25", "title_unescape^1.25", "text", "title_bigram^1.25", "title_unescape_bigram^1.25", "text_bigram"]
                    }
                }
        res = self.client.search(index=WIKIPEDIA_INDEX_NAME, query = constructed_query, size = max(topn, rerank_topn))

        res = [self._extract_one(x, lazy=lazy) for x in res['hits']['hits']]
        res = self.rerank_with_query(query, res)[:topn]
        # print(res)
        res = [{'title': _['title'], 'text': _['text']} for _ in res]
        return res

    def search(self, question, k=10):
        try:
            res = self.single_text_query(query = question, topn = k)
            return json.dumps(res, ensure_ascii=False)
        except Exception as err:
            print(Exception, err)


@app.route('/', methods=['POST', 'GET'])
@cross_origin()
def main():
    global ES
    question = request.json['query']
    k = int(request.json['k'])
    return ES.search(question, k)
    

if __name__ == '__main__':
    ES = ElasticSearch()
    app.run(host='0.0.0.0', port=1439, threaded = True)