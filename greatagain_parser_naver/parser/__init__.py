# -*- coding: utf-8 -*-


class Parser(object):

    def __init__(self, repository):
        self.repository = repository

    def save_comments_count_history(self, article_uid, comments_count):
        self.repository.save_comments_count_history(article_uid, comments_count)

    def save_article(self, article):
        self.repository.save_article(article)

    def save_comments(self, article_uid, comment_list):
        self.repository.save_comments(article_uid, comment_list)
