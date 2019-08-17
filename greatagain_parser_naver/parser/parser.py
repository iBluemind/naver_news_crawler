# -*- coding: utf-8 -*-

from typing import List
from greatagain_parser_naver.crawler.dao import MongoRepository
from greatagain_parser_naver.parser.model import Article, Comment, CommentsCountHistory


class Parser(object):
    def __init__(self, repository: MongoRepository):
        self.repository = repository

    async def save_article(self, article: Article):
        await self.repository.save_article(article)

    async def save_comments_count_history(self, comments_count_history: CommentsCountHistory):
        await self.repository.save_comments_count_history(comments_count_history)

    async def save_comments(self, article_uid: str, comments: List[Comment]):
        await self.repository.save_comments(article_uid, comments)
