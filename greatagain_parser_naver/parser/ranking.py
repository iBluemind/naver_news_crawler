# -*- coding: utf-8 -*-

# 랭킹뉴스 - 많이 본 뉴스 : http://m.news.naver.com/rankingList.nhn
# 정치 : http://m.news.naver.com/rankingList.nhn?sid1=100&date=20180127
# 경제 : http://m.news.naver.com/rankingList.nhn?sid1=101&date=20180127
# 사회 : http://m.news.naver.com/rankingList.nhn?sid1=102&date=20180127
# 생활 : http://m.news.naver.com/rankingList.nhn?sid1=103&date=20180127
# 세계 : http://m.news.naver.com/rankingList.nhn?sid1=104&date=20180127
# 연예 : http://m.news.naver.com/rankingList.nhn?sid1=106&date=20180127

# 랭킹뉴스 - 공감많은 : http://m.news.naver.com/likeRankingList.nhn
# 랭킹뉴스 - 댓글많은 : http://m.news.naver.com/memoRankingList.nhn
# 랭킹뉴스 - SNS 공유 : http://m.news.naver.com/shareRankingList.nhn

# 뉴스홈 : http://news.naver.com/main/home.nhn


import logging, hashlib, asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from greatagain_parser_naver.parser import Parser
from greatagain_parser_naver.crawler.client import get, post
from greatagain_parser_naver.crawler.utils import parse_jquery_jsonp, generate_jquery_jsonp_nonce
from greatagain_parser_naver.parser.exceptions import ParseResponseError

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


NAVER_NEWS_MOBILE_HOST = 'https://m.news.naver.com'
NAVER_API_HOST = 'https://apis.naver.com'

NAVER_NEWS_CATEGORY_POLITICS = 100
NAVER_NEWS_CATEGORY_ECONOMY = 101
NAVER_NEWS_CATEGORY_SOCIAL = 102
NAVER_NEWS_CATEGORY_LIFE = 103
NAVER_NEWS_CATEGORY_WORLD = 104
NAVER_NEWS_CATEGORY_ENTERTAINMENTS = 106

comment_templates = {
    NAVER_NEWS_CATEGORY_POLITICS: 'default_politics',
    NAVER_NEWS_CATEGORY_ECONOMY: 'default_economy',
    NAVER_NEWS_CATEGORY_SOCIAL: 'default_society',
    NAVER_NEWS_CATEGORY_LIFE: 'view_life',
    NAVER_NEWS_CATEGORY_WORLD: 'default_world',
    NAVER_NEWS_CATEGORY_ENTERTAINMENTS: 'default_ent'
}


def get_article_uid(oid, aid):
    return hashlib.md5("{}{}".format(oid, aid).encode()).hexdigest()


class RankingNewsParser(Parser):
    async def run(self, category, date):
        self.category = category
        self.date = date

        async for link, ranking_read in get_ranking_list(category, date):
            future = asyncio.ensure_future(self._parse(link, ranking_read))
            await asyncio.wait_for(future, None)

    async def _parse(self, link, article):
        parsed_link = urlparse(link)
        link_parameters = parse_qs(parsed_link.query)

        oid = link_parameters['oid'][0]
        aid = link_parameters['aid'][0]
        uid = get_article_uid(oid, aid)

        comments_count = await get_comments_count(oid, aid)
        await self.save_comments_count_history(uid, comments_count)

        news_article = parse_ranking_read(uid, comments_count, article.text, oid, aid)
        await self.save_article(news_article)

        logger.info('| Current rankingRead : {}'.format(news_article))
        await get_comments(self.category, self.date, oid, aid, comment_templates[self.category],
                           self.save_comments)


async def get_comments_count(oid, aid):
    url = '{}/commonComment/listCount.nhn'.format(NAVER_NEWS_MOBILE_HOST)
    response = await post(url, data={'lang': 'ko', 'ticket': 'news', 'gnos': 'news{},{}'.format(oid, aid)})
    parsed = response.json()
    return parsed['message']['result'][0]['count']


def parse_ranking_read(uid, comments_count, ranking_read, oid, aid):
    soup = BeautifulSoup(ranking_read, "lxml")
    article = {
        'uid': uid,
        'title': soup.select("h2.media_end_head_headline")[0].text,
        'content': soup.select("._news_article_body")[0].text.strip(),
        'comments_count': comments_count,
        'initialized_at': soup.select(".media_end_head_info_datestamp_time")[0].text,
        'url': 'https://news.naver.com/main/read.nhn?oid={}&aid={}'.format(oid, aid)
    }

    if len(soup.select(".media_end_head_info_datestamp_time")) > 1:
        article['finalized_at'] = soup.select(".media_end_head_info_datestamp_time")[1].text
    return article


async def get_ranking_list(category, date):
    response = await get('{}/rankingList.nhn?sid1={}&date={}'.format(NAVER_NEWS_MOBILE_HOST, category, date))
    soup = BeautifulSoup(response.text, 'lxml')

    titles = soup.find_all(class_="commonlist_tx_headline")

    logger.info('| Parsed Ranking list...')
    [logger.info('{}: {}'.format(i, title)) for i, title in enumerate(list(map(lambda x: x.text, titles)))]

    links = soup.select("ul.commonlist > li > a")
    for link in list(map(lambda x: x.get('href'), links)):
        ranking_read = await get('{}{}'.format(NAVER_NEWS_MOBILE_HOST, link))
        yield link, ranking_read


def parse_child_comment_list(child_comment_list):
    try:
        return list(map(lambda comment: {
            'uid': comment['commentNo'],
            'parent_uid': comment['parentCommentNo'],
            'user_id': comment['userIdNo'],
            'username': comment['maskedUserId'],
            'nickname': comment['maskedUserName'],
            'content': comment['contents'],
            'like_count': comment['sympathyCount'],
            'dislike_count': comment['antipathyCount'],
            'registered_at': comment['regTime'],
            'modified_at': comment['modTime'],
        }, child_comment_list))
    except:
        raise ParseResponseError


def parse_comment_list(comment_list):
    try:
        return list(map(lambda comment: {
            'uid': comment['commentNo'],
            'user_id': comment['userIdNo'],
            'username': comment['maskedUserId'],
            'nickname': comment['maskedUserName'],
            'content': comment['contents'],
            'reply_count': comment['replyCount'],
            'like_count': comment['sympathyCount'],
            'dislike_count': comment['antipathyCount'],
            'registered_at': comment['regTime'],
            'modified_at': comment['modTime'],
        }, comment_list))
    except:
        raise ParseResponseError


async def _request_comment_list(category, date, url, oid, aid):
    response = await get(
        url,
        headers={
            'Referer': '{}/comment/list.nhn?gno=news{}%2c{}&aid={}&ntype=RANKING&oid={}&sid1={}&backUrl=%2frankingList.nhn%3fsid1%3d{}%26date%3d{}&light=off&date={}'.format(
                NAVER_NEWS_MOBILE_HOST, oid, aid, aid, oid, category, category, date, date
            )
        }
    )
    parsed_response = parse_jquery_jsonp(response)

    has_next_page = int(parsed_response['result']['pageModel']['nextPage']) > 0
    return parsed_response, has_next_page


async def _get_comments(category, date, oid, aid, template, parsed_response):
    parsed_comment_list = parse_comment_list(parsed_response['result']['commentList'])
    has_replies = list(filter(lambda comment: int(comment['reply_count']) > 0, parsed_comment_list))
    for comment in has_replies:
        child_comments = await get_child_comments(category, date, oid, aid, template, comment)
        comment['children'] = child_comments
    return parsed_comment_list


async def get_first_page_comments(category, date, oid, aid, template, save_callback):
    logger.info('| Reading {},{}\'s comments first page...'.format(oid, aid))

    jquery = generate_jquery_jsonp_nonce()
    url = '{}/commentBox/cbox/web_neo_list_jsonp.json?ticket=news&templateId={}&pool=cbox5&_callback={}&lang=ko&country=&objectId=news{}%2C{}&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&page=1&initialize=true&userType=&useAltSort=true&replyPageSize=20&moveTo=&sort=new&includeAllStatus=true&_={}'.format(
        NAVER_API_HOST, template, jquery['jsonp_key'], oid, aid, jquery['nonce']
    )

    parsed_response, has_next_page = await _request_comment_list(category, date, url, oid, aid)
    total_pages = parsed_response['result']['pageModel']['totalPages']
    parsed_comment_list = await _get_comments(category, date, oid, aid, template, parsed_response)

    await save_callback(get_article_uid(oid, aid), parsed_comment_list)
    return parsed_comment_list, total_pages


async def get_more_page_comments(category, date, oid, aid, template, page, save_callback):
    logger.info('| Reading {},{}\'s comments {} page...'.format(oid, aid, page))
    jquery = generate_jquery_jsonp_nonce()
    url = '{}/commentBox/cbox/web_neo_list_jsonp.json?ticket=news&templateId={}&pool=cbox5&_callback={}&lang=ko&country=&objectId=news{}%2C{}&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&page={}&refresh=false&sort=NEW&includeAllStatus=true&_={}'.format(
            NAVER_API_HOST, template, jquery['jsonp_key'], oid, aid, page, jquery['nonce'])
    parsed_response, has_next_page = await _request_comment_list(category, date, url, oid, aid)

    parsed_comment_list = await _get_comments(category, date, oid, aid, template, parsed_response)
    await save_callback(get_article_uid(oid, aid), parsed_comment_list)
    return parsed_comment_list


async def get_first_page_child_comments(category, date, oid, aid, parent, template):
    logger.info(
        '| Reading {},{}\'s {}\'s child comments first page ...'.format(oid, aid, parent))
    jquery = generate_jquery_jsonp_nonce()
    url = '{}/commentBox/cbox/web_neo_list_jsonp.json?ticket=news&templateId={}&pool=cbox5&_callback={}&lang=ko&country=&objectId=news{}%2C{}&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&parentCommentNo={}&page=1&userType=&includeAllStatus=true&moreType=next&_={}'.format(
            NAVER_API_HOST, template, jquery['jsonp_key'], oid, aid, parent, jquery['nonce'])
    parsed_child_response, has_child_next_page = await _request_comment_list(category, date, url, oid, aid)

    total_pages = parsed_child_response['result']['pageModel']['totalPages']
    parsed_child_comment_list = parse_child_comment_list(parsed_child_response['result']['commentList'])
    logger.info('| Parsed child commentlist : {}'.format(parsed_child_comment_list))
    return parsed_child_comment_list, total_pages


async def get_more_page_child_comments(category, date, oid, aid, parent, template, page):
    logger.info(
        '| Reading {},{}\'s {}\'s child comments {} page ...'.format(oid, aid, parent, page))

    jquery = generate_jquery_jsonp_nonce()
    url = '{}/commentBox/cbox/web_neo_list_jsonp.json?ticket=news&templateId={}&pool=cbox5&_callback={}&lang=ko&country=&objectId=news{}%2C{}&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&parentCommentNo={}&page={}&userType=&includeAllStatus=true&moreType=next&_={}'.format(
            NAVER_API_HOST, template, jquery['jsonp_key'], oid, aid, parent, page, jquery['nonce'])
    parsed_child_response, has_child_next_page = await _request_comment_list(category, date, url, oid, aid)

    parsed_child_comment_list = parse_child_comment_list(parsed_child_response['result']['commentList'])
    logger.info('| Parsed child commentlist : {}'.format(parsed_child_comment_list))
    return parsed_child_comment_list


async def get_child_comments(category, date, oid, aid, template, comment):
    child_comments, child_end_page = await get_first_page_child_comments(category, date, oid, aid,
                                                                         comment['uid'], template)
    futures = [asyncio.ensure_future(get_more_page_child_comments(category, date, oid, aid,
                                                                  comment['uid'], template, page))
               for page in range(2, child_end_page)]
    parsed_child_comment_lists = await asyncio.gather(*futures)

    more_child_comments = [parsed_child_comments for parsed_child_comment_list in parsed_child_comment_lists
                           for parsed_child_comments in parsed_child_comment_list]
    child_comments.extend(more_child_comments)
    return child_comments


async def get_comments(category, date, oid, aid, template, save_callback):
    comments, end_page = await get_first_page_comments(category, date, oid, aid,
                                                       template, save_callback)

    futures = [asyncio.ensure_future(get_more_page_comments(category, date, oid, aid,
                               template, page, save_callback))
               for page in range(2, end_page)]
    parsed_comment_lists = await asyncio.gather(*futures)

    more_comments = [parsed_comments for parsed_comment_list in parsed_comment_lists
             for parsed_comments in parsed_comment_list]
    comments.extend(more_comments)

    return comments
