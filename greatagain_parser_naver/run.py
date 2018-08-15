# -*- coding: utf-8 -*-

# 30초에 7개 요청 정도


import logging, datetime
from greatagain_parser_naver.parser.ranking import RankingNewsParser, NAVER_NEWS_CATEGORY_POLITICS, \
    NAVER_NEWS_CATEGORY_ECONOMY, \
    NAVER_NEWS_CATEGORY_SOCIAL, \
    NAVER_NEWS_CATEGORY_LIFE, \
    NAVER_NEWS_CATEGORY_WORLD, \
    NAVER_NEWS_CATEGORY_ENTERTAINMENTS


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


if __name__ == '__main__':
    categories = [
        NAVER_NEWS_CATEGORY_POLITICS,
        NAVER_NEWS_CATEGORY_ECONOMY,
        NAVER_NEWS_CATEGORY_SOCIAL,
        NAVER_NEWS_CATEGORY_LIFE,
        NAVER_NEWS_CATEGORY_WORLD,
        NAVER_NEWS_CATEGORY_ENTERTAINMENTS
    ]

    date = datetime.datetime.today().strftime('%Y%m%d')
    ranking_news_parser = RankingNewsParser()

    for category in categories:
        ranking_news_parser.run(category, date)
