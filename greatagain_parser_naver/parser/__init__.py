# -*- coding: utf-8 -*-


class Parser(object):

    def __init__(self, repository):
        self.repository = repository

    async def save_comments_count_history(self, article_uid, comments_count):
        await self.repository.save_comments_count_history(article_uid, comments_count)

    async def save_article(self, article):
        await self.repository.save_article(article)

    async def save_comments(self, article_uid, comment_list):
        await self.repository.save_comments(article_uid, comment_list)
