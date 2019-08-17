# -*- coding: utf-8 -*-

from typing import List
from greatagain_parser_naver.crawler.dao import MongoRepository
from greatagain_parser_naver.parser.model import Article, Comment


class Parser(object):
    def __init__(self, repository: MongoRepository):
        self.repository = repository

    async def save_article(self, article: Article):
        await self.repository.save_article(article)

    async def save_comments_count_history(self, article_uid: str, comments_count: int):
        await self.repository.save_comments_count_history(article_uid, comments_count)

    async def save_comments(self, article_uid: str, comments: List[Comment]):
        await self.repository.save_comments(article_uid, comments)
