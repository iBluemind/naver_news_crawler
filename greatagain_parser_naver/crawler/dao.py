# -*- coding: utf-8 -*-

import six, abc, datetime
import motor.motor_asyncio
from abc import abstractmethod
from greatagain_parser_naver.parser.model import Comment, Article
from typing import List


@six.add_metaclass(abc.ABCMeta)
class Repository(object):

    @abstractmethod
    async def save_comments_count_history(self, article_uid, comments_count):
        raise NotImplementedError

    @abstractmethod
    async def save_article(self, article):
        raise NotImplementedError

    @abstractmethod
    async def save_comments(self, article_uid, comment_list):
        raise NotImplementedError


class MongoRepository(Repository):
    def __init__(self, uri: str, database_name: str):
        self.connection = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.database = self.connection.get_database(database_name)

        self.articles = self.database.get_collection('articles')
        self.comments_count_histories = self.database.get_collection('comments_count_histories')
        self.comments = self.database.get_collection('comments')

    async def save_comments_count_history(self, article_uid: str, comments_count: int):
        document = {
            'article_uid': article_uid,
            'comments_count': comments_count,
            'created_at': datetime.datetime.now(),
        }

        await self.comments_count_histories.insert_one(document)


    async def save_article(self, article: Article):
        where = {'uid': article.uid}
        operation = {'$set': article.__dict__}

        await self.articles.update_one(where, operation, upsert=True)


    async def save_comments(self, article_uid: str, comment_list: List[Comment]):
        def convert_comment(comment: Comment):
            comment.article_uid = article_uid
            return comment

        converted_comments = list(map(lambda comment: convert_comment(comment), comment_list))

        for comment in converted_comments:
            where = {'uid': comment.uid}

            serialized_comment = comment.__dict__

            # TODO
            if serialized_comment.get('children'):
                serialized_comment['children'] = [child.__dict__ for child in comment.children]

            operation = {'$set': serialized_comment}

            await self.comments.update_one(where, operation, upsert=True)

    def close(self):
        if self.connection:
            self.connection.close()
