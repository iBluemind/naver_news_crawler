# -*- coding: utf-8 -*-

# 30초에 7개 요청 정도


import logging, datetime, asyncio
from config import DATABASE_URI, DATABASE_NAME
from greatagain_parser_naver.crawler.client import session
from greatagain_parser_naver.crawler.dao import MongoRepository
from greatagain_parser_naver.parser.ranking import RankingNewsParser, NAVER_NEWS_CATEGORY_POLITICS, \
    NAVER_NEWS_CATEGORY_ECONOMY, \
    NAVER_NEWS_CATEGORY_SOCIAL, \
    NAVER_NEWS_CATEGORY_LIFE, \
    NAVER_NEWS_CATEGORY_WORLD, \
    NAVER_NEWS_CATEGORY_ENTERTAINMENTS


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def main():
    repository = MongoRepository(DATABASE_URI, DATABASE_NAME)

    categories = [
        NAVER_NEWS_CATEGORY_POLITICS,
        NAVER_NEWS_CATEGORY_ECONOMY,
        NAVER_NEWS_CATEGORY_SOCIAL,
        NAVER_NEWS_CATEGORY_WORLD,
    ]

    date = datetime.datetime.today().strftime('%Y%m%d')
    ranking_news_parser = RankingNewsParser(repository)

    futures = [asyncio.create_task(ranking_news_parser.run(category, date)) for category in categories]

    try:
        await asyncio.gather(*futures)
    finally:
        await ranking_news_parser.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
