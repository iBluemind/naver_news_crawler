import six, abc, datetime, functools
from greatagain_parser_naver import loop
from abc import abstractmethod
from pymongo import MongoClient


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
    def __init__(self, uri, database_name):
        self.connection = MongoClient(uri)
        self.database = self.connection.get_database(database_name)

        self.articles = self.database.get_collection('articles')
        self.comments_count_histories = self.database.get_collection('comments_count_histories')
        self.comments = self.database.get_collection('comments')

    async def save_comments_count_history(self, article_uid, comments_count):
        await loop.run_in_executor(None, functools.partial(self.comments_count_histories.insert_one, {
            'article_uid': article_uid,
            'comments_count': comments_count,
            'created_at': datetime.datetime.now(),
        }))


    async def save_article(self, article):
        await loop.run_in_executor(None, functools.partial(
            self.articles.update_one, {'uid': article['uid']},
                                     {'$set': article},
                                     upsert=True)
        )


    async def save_comments(self, article_uid, comment_list):
        def convert_comment(comment):
            comment['article_uid'] = article_uid
            return comment

        converted_comments = list(map(lambda comment: convert_comment(comment), comment_list))
        for comment in converted_comments:
            await loop.run_in_executor(None, functools.partial(
                self.comments.update_one, {'uid': comment['uid']},
                                         {'$set': comment},
                                         upsert=True)
            )
