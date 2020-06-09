# -*- coding: utf-8 -*-

from elasticsearch_dsl import Document, Date, Completion, Keyword, Text, Integer
from elasticsearch_dsl.connections import connections
connections.create_connection(hosts=["localhost"])

class jobType(Document):
    class Meta:# 设置index名称和document名称
        index = "scene"
        doc_type = "_doc"

    class Index:
        name = "scene"
        doc_type = "_doc"

    name = Text(analyzer="ik_max_word")  # 景点名称
    address = Text(analyzer="ik_max_word")  # 景点地址
    open_time = Text(analyzer="ik_max_word")  # 开放时间
    brief = Text(analyzer="ik_max_word")  # 景点简介
    ticket = Text(analyzer="ik_max_word")  # 门票价格
    score = Text(analyzer="ik_max_word")  # 景点评分
    site = Text(analyzer="ik_max_word")  # 网站来源
    url_pic = Text(analyzer="ik_max_word")  # 景点图片url

    suggest = Completion()  # 搜索建议

