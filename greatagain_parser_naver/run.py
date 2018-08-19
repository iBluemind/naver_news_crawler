# -*- coding: utf-8 -*-

# 30초에 7개 요청 정도


import logging, datetime
from config import DATABASE_HOST, DATABASE_NAME, DATABASE_PORT, DATABASE_PASSWORD, DATABASE_USERNAME
from greatagain_parser_naver.crawler.dao import MongoRepository
from greatagain_parser_naver.parser.ranking import RankingNewsParser, NAVER_NEWS_CATEGORY_POLITICS, \
    NAVER_NEWS_CATEGORY_ECONOMY, \
    NAVER_NEWS_CATEGORY_SOCIAL, \
    NAVER_NEWS_CATEGORY_LIFE, \
    NAVER_NEWS_CATEGORY_WORLD, \
    NAVER_NEWS_CATEGORY_ENTERTAINMENTS


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


if __name__ == '__main__':
    repository = MongoRepository(DATABASE_HOST, DATABASE_PORT,
                                 DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_NAME)

    categories = [
        NAVER_NEWS_CATEGORY_POLITICS,
        NAVER_NEWS_CATEGORY_SOCIAL,
    ]

    date = datetime.datetime.today().strftime('%Y%m%d')
    ranking_news_parser = RankingNewsParser(repository)

    for category in categories:
        ranking_news_parser.run(category, date)
