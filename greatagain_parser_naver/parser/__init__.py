# -*- coding: utf-8 -*-

import datetime
from greatagain_parser_naver.crawler.dao import articles, comments, comments_count_history


class Parser(object):
    def save_comments_count_history(self, article_uid, comments_count):
        comments_count_history.insert_one({
            'article_uid': article_uid,
            'comments_count': comments_count,
            'created_at': datetime.datetime.now(),
        })

    def save_article(self, article):
        articles.update_one({'uid': article['uid']},
                            {'$set': article},
                            upsert=True)

    def save_comments(self, article_uid, comment_list):
        def convert_comment(comment):
            comment['article_uid'] = article_uid
            return comment
        converted_comments = list(map(lambda comment: convert_comment(comment), comment_list))
        for comment in converted_comments:
            comments.update_one({'uid': comment['uid']},
                                {'$set': comment},
                                upsert=True)
