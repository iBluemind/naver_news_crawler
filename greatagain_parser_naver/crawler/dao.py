# -*- coding: utf-8 -*-

import six, abc, logging
import motor.motor_asyncio
from abc import abstractmethod
from greatagain_parser_naver.parser.model import Comment, Article, CommentsCountHistory
from typing import List


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class Repository(object):

    @abstractmethod
    async def save_comments_count_history(self, comments_count_history: CommentsCountHistory):
        raise NotImplementedError

    @abstractmethod
    async def save_article(self, article: Article):
        raise NotImplementedError

    @abstractmethod
    async def save_comments(self, article_uid: str, comment_list: List[Comment]):
        raise NotImplementedError


class MongoRepository(Repository):
    def __init__(self, uri: str, database_name: str):
        self.connection = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.database = self.connection.get_database(database_name)

        self.articles = self.database.get_collection('articles')
        self.comments_count_histories = self.database.get_collection('comments_count_histories')
        self.comments = self.database.get_collection('comments')

    async def save_comments_count_history(self, comments_count_history: CommentsCountHistory):
        logger.debug('Insert {}\'s CommentCountHistory'.format(comments_count_history.article_uid))
        await self.comments_count_histories.insert_one(comments_count_history.__dict__)

    async def save_article(self, article: Article):
        where = {'uid': article.uid}
        operation = {'$set': article.__dict__}

        logger.debug('Update Article {}'.format(article.uid))
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

            logger.debug('Update Comment {}'.format(comment.uid))
            await self.comments.update_one(where, operation, upsert=True)

    def close(self):
        if self.connection:
            self.connection.close()
