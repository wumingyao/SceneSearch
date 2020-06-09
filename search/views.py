import json
from django.shortcuts import render
from django.views.generic.base import View
from django.http import HttpResponse
from elasticsearch import Elasticsearch
from datetime import datetime
import redis
from django.views.generic.base import View
import base64
import requests
from urllib import request
import ssl
import json
from rest_framework import viewsets
from operator import itemgetter
from itertools import groupby

client = Elasticsearch(hosts=["127.0.0.1"])
redis_cli = redis.StrictRedis()

response = client.search(
    index="scene",
    body={
    }
)
redis_cli.set("jobbole_count", response['hits']['total']['value'])


def list2str(str, mode=0):
    if mode == 0:
        if isinstance(str, list):
            str_new = ''.join(str)
            return str_new
        else:
            return str
    elif mode == 1:
        if isinstance(str, list):
            str_new = str[0]
            return str_new
        else:
            return str



def isFloat(x):
    try:
        float(x)
        if str(x) in ['inf', 'infinity', 'INF', 'INFINITY', 'True', 'NAN', 'nan', 'False', '-inf', '-INF', '-INFINITY', '-infinity', 'NaN', 'Nan']:
            return False
        else:
            return True
    except:
        return False


def str2float(str, mode=0):
    if mode == 0:
        if isFloat(str):
            return float(str)
        else:
            return 0.0


class IndexView(View):
    # 首页
    def get(self, request):
        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=6)
        topn_search = [item.decode('utf8') for item in topn_search]
        print(topn_search)
        result = []
        for key_word in topn_search:
            response = client.search(
                index="scene",
                body={
                    "_source": ["name", "url_pic"],
                    "query": {
                        "multi_match": {
                            "query": key_word,
                            "fields": ["name", "brief"]
                        }
                    },
                    "size": 1
                }
            )
            for hit in response['hits']['hits']:
                # result.append(suggest_scene['_source'])
                hit_dict = {}
                hit_dict["name"] = list2str(hit["_source"]["name"])
                hit_dict["url_pic"] = list2str(hit["_source"]["url_pic"], mode=1)
                result.append(hit_dict)

        print(result)
        return render(request, "index.html", {"result_search": result})


# Create your views here.
class SearchSuggest(View):
    def get(self, request):
        key_words = request.GET.get('s', '')  # 获取url中参数s的值
        re_datas = []

        if key_words:
            # suggest官网https://www.elastic.co/guide/en/elasticsearch/reference/current/search-suggesters.html
            # TODO:completion的方法
            # response = client.search(
            #     index="51job6",
            #     body={
            #         "suggest": {
            #             "my_suggest": {
            #                 "prefix": key_words,
            #                 "completion": {
            #                     "field": "suggest",
            #                     "fuzzy": {
            #                         "fuzziness": 10
            #                     },
            #                     "size": 10
            #                 }
            #             }
            #         }
            #     }
            # )
            # suggestions = response["suggest"]["my_suggest"][0]['options']
            # for match in suggestions:
            #     source = match['_source']
            #     re_datas.append(source["job_name"])

            # TODO:match的方法
            response = client.search(
                index="scene",
                body={
                    "_source": "name",
                    "query": {
                        "multi_match": {
                            "query": key_words,
                            "fields": ["name", "brief"]
                        }
                    },
                    "size": 5
                }
            )
            for hit in response["hits"]["hits"]:
                re_datas.append(hit["_source"]["name"])

            re_datas = list(set(re_datas))
        return HttpResponse(json.dumps(re_datas), content_type="application/json")


class SearchView(View):

    def get(self, request):
        # 获取搜索关键字
        key_words = request.GET.get("q", "")
        # 获取当前选择搜索的范围
        s_type = request.GET.get("s_type", "scene")

        redis_cli.zincrby("search_keywords_set", 1, key_words)  # 该key_words的搜索记录+1

        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=5)
        topn_search = [item.decode('utf8') for item in topn_search]
        page = request.GET.get("p", "1")
        try:
            page = int(page)
        except:
            page = 1
        # 从redis查看该类数据总量
        jobbole_count = redis_cli.get("jobbole_count").decode('utf8')
        start_time = datetime.now()
        # 根据关键字查找
        response = client.search(
            index="scene",
            body={
                "query": {
                    "multi_match": {
                        "query": key_words,
                        "fields": ["name", "brief"]
                    }
                },
                "from": (page - 1) * 10,
                "size": 5,
                # 对关键字进行高光标红处理
                "highlight": {
                    "pre_tags": ['<span class="keyWord">'],
                    "post_tags": ['</span>'],
                    "fields": {
                        "name": {},
                        "brief": {},
                    }
                }
            }
        )

        end_time = datetime.now()
        last_seconds = (end_time - start_time).total_seconds()
        total_nums = response["hits"]["total"]['value']
        if (page % 10) > 0:
            page_nums = int(total_nums / 10) + 1
        else:
            page_nums = int(total_nums / 10)
        hit_list = []
        print(str(response["hits"]["hits"][0]["_id"]))
        for hit in response["hits"]["hits"]:
            hit_dict = {}
            # if "job_name" in hit["highlight"]:
            #     hit_dict["job_name"] = "".join(hit["highlight"]["job_name"])
            # else:
            #     hit_dict["job_name"] = hit["_source"]["job_name"]
            # if "company_detail" in hit["highlight"]:
            #     hit_dict["company_detail"] = "".join(hit["highlight"]["company_detail"])[:500]
            # else:
            #     hit_dict["company_detail"] = hit["_source"]["company_detail"][:500]
            if hit["_source"]["brief"]:
                hit_dict["brief"] = list2str(hit["_source"]["brief"])[:500]
            hit_dict["name"] = list2str(hit["_source"]["name"])
            hit_dict["open_time"] = list2str(hit["_source"]["open_time"])
            hit_dict["url_pic"] = list2str(hit["_source"]["url_pic"], mode=1)
            hit_dict["score"] = str2float(list2str(hit["_source"]["score"]))
            hit_dict["address"] = list2str(hit["_source"]["address"])
            hit_dict["ticket"] = list2str(hit["_source"]["ticket"])
            hit_dict["site"] = list2str(hit["_source"]["site"])
            hit_dict['id'] = list2str(hit['_id'])

            hit_list.append(hit_dict)
        hit_list.sort(key=itemgetter('score'), reverse=True)

        hit_list_all = []
        r = client.search(
            index="scene",
            body={
                "query": {
                    "multi_match": {
                        "query": key_words,
                        "fields": ["name", "brief"]
                    }

                },
                "size": 10000
            }
        )
        for hit in r["hits"]["hits"]:
            hit_dict = {}
            hit_dict["site"] = list2str(hit["_source"]["site"])

            hit_list_all.append(hit_dict)
        hit_list_all.sort(key=itemgetter('site'))
        siteCount = []
        for site, group in groupby(hit_list_all, key=itemgetter('site')):
            dict = {}
            dict['site'] = site
            dict['count'] = len(list(group))
            siteCount.append(dict)
        return render(request, "result.html", {"page": page,
                                               "all_hits": hit_list,
                                               "key_words": key_words,
                                               "total_nums": total_nums,
                                               "page_nums": page_nums,
                                               "last_seconds": last_seconds,
                                               "jobbole_count": jobbole_count,
                                               "topn_search": topn_search,
                                               "siteCount": siteCount})


class SoutuView(viewsets.ViewSet):
    def soutu(self, request):
        # gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        # # client_id 为官网获取的AK， client_secret 为官网获取的SK
        # host = 'https://aip.baidubce.com/oauth/2.0/token?grant_' \
        #        'type=client_credentials&client_id=BeA79RDyo7NAYsFEXGeuS243&client_secret=Q8tUGvRh4PSGsT5ZkiTOy3xmlLC0AGzl'
        # req = request.Request(host)
        # response = request.urlopen(req, context=gcontext).read().decode('UTF-8')
        # result = json.loads(response)
        # if (result):
        #     print(result)
        if request.method == 'POST':
            myfile = request.FILES.get('file', None)
            if myfile is None:
                result = {"key_words": '故宫'}
                return HttpResponse(json.dumps(result), content_type="application/json")
            img = base64.b64encode(myfile.read())
            host = 'https://aip.baidubce.com/rest/2.0/image-classify/v2/advanced_general'
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            access_token = '24.10f79847cb8c412feb9c23af71e72b9f.2592000.1593048885.282335-20065393'
            host = host + '?access_token=' + access_token
            data = {}
            data['access_token'] = access_token
            data['image'] = img
            res = requests.post(url=host, headers=headers, data=data)
            req = res.json()
            result = req['result']
            if len(result) > 0:
                key_words = result[0]['keyword']
                result = {"key_words": key_words}
            else:
                result = {"key_words": '无法识别'}
            return HttpResponse(json.dumps(result), content_type="application/json")


class DetailView(View):
    def get(self, request):
        url_pic = request.GET.get("_up", "")
        # _id = '80XIaXIB3S7bAbbB0JRa'
        # 查找对应记录
        response = client.search(
            index="scene",
            body={
                "query": {
                    'match': {
                        'url_pic': url_pic
                    }
                }
            }
        )
        hit_dict = {}
        hit = response["hits"]["hits"][0]
        if hit["_source"]["brief"]:
            hit_dict["brief"] = list2str(hit["_source"]["brief"])
        hit_dict["name"] = list2str(hit["_source"]["name"])
        hit_dict["open_time"] = list2str(hit["_source"]["open_time"])
        hit_dict["url_pic"] = list2str(hit["_source"]["url_pic"], mode=1)
        hit_dict["score"] = list2str(hit["_source"]["score"])
        hit_dict["address"] = list2str(hit["_source"]["address"])
        hit_dict["ticket"] = list2str(hit["_source"]["ticket"])
        hit_dict["site"] = list2str(hit["_source"]["site"])
        print(hit_dict)
        return render(request, 'detail.html', {'hit': hit_dict})
