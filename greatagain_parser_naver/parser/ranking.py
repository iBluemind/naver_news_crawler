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
import greatagain_parser_naver.crawler.client as client
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from typing import List, Tuple, Optional
from greatagain_parser_naver.crawler.client import get, post
from greatagain_parser_naver.crawler.utils import parse_jquery_jsonp, generate_jquery_jsonp_nonce
from greatagain_parser_naver.parser.exceptions import ParseResponseError
from greatagain_parser_naver.parser.model import Article, ChildComment, Comment, CommentsCountHistory, ArticleHistory
from greatagain_parser_naver.parser.parser import Parser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


NAVER_NEWS_MOBILE_HOST = 'https://m.news.naver.com'
NAVER_API_HOST = 'https://apis.naver.com'
NAVER_NEWS_LIKE_HOST = 'https://news.like.naver.com'

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


def get_article_uid(oid: str, aid: str) -> str:
    return hashlib.md5("{}{}".format(oid, aid).encode()).hexdigest()


class RankingNewsParser(Parser):
    async def run(self, category: int, date: str):
        self.category = category
        self.date = date

        async for link, ranking_read in get_ranking_list(category, date):
            await self._parse(link, ranking_read)

    async def _parse(self, link: str, article: str):
        parsed_link = urlparse(link)
        link_parameters = parse_qs(parsed_link.query)

        oid = link_parameters['oid'][0]
        aid = link_parameters['aid'][0]
        uid = get_article_uid(oid, aid)

        comments_count = await get_comments_count(oid, aid)
        await self.save_comments_count_history(
            CommentsCountHistory(
                article_uid=uid,
                comments_count=comments_count,
            )
        )

        news_article = await parse_ranking_read(uid, comments_count, article, oid, aid)

        await self.save_article(news_article)
        await self.save_article_history(
            ArticleHistory(
                article_uid=news_article.uid,
                title=news_article.title,
                content=news_article.content,
                comments_count=news_article.comments_count,
                reactions=news_article.reactions,
                recommends=news_article.recommends
            )
        )

        await client.hang_like_human()

        logger.info('* Current rankingRead : {}'.format(news_article))
        await get_comments(self.category, self.date, oid, aid,
                           comment_templates[self.category], self.save_comments)

    async def close(self):
        await client.close()
        self.repository.close()


async def get_reactions_count(oid: str, aid: str, q: str) -> Tuple[int, Optional[int]]:
    jquery = generate_jquery_jsonp_nonce()

    url = '{}/v1/search/contents?suppress_response_codes=true&callback={}&q={}&isDuplication=false&_={}'.format(
        NAVER_NEWS_LIKE_HOST, jquery['jsonp_key'], q, jquery['nonce']
    )

    request = await get(
        url,
        headers={
            'Referer': '{}/rankingRead.nhn?oid={}&aid={}'.format(
                NAVER_NEWS_MOBILE_HOST, oid, aid
            )
        }
    )

    response = await request.text()

    parsed_response = parse_jquery_jsonp(response)
    contents = parsed_response['contents']

    total_reactions: int = 0
    recommends: int = 0

    article_reactions = list(filter(lambda x: x['serviceId'] == 'NEWS', contents))
    if article_reactions:
        article_reactions = article_reactions[0]['reactions']

        angry_reaction = list(filter(lambda x: x['reactionType'] == 'angry', article_reactions))
        angry: int = angry_reaction[0]['count'] if angry_reaction else 0

        warm_reaction = list(filter(lambda x: x['reactionType'] == 'warm', article_reactions))
        warm: int = warm_reaction[0]['count'] if warm_reaction else 0

        want_reaction = list(filter(lambda x: x['reactionType'] == 'want', article_reactions))
        want: int = want_reaction[0]['count'] if want_reaction else 0

        like_reaction = list(filter(lambda x: x['reactionType'] == 'like', article_reactions))
        like: int = like_reaction[0]['count'] if like_reaction else 0

        sad_reaction = list(filter(lambda x: x['reactionType'] == 'sad', article_reactions))
        sad: int = sad_reaction[0]['count'] if sad_reaction else 0

        total_reactions = angry + warm + want + like + sad

    journalist_reactions = list(filter(lambda x: x['serviceId'] == 'JOURNALIST', contents))
    if journalist_reactions:
        journalist_reactions = journalist_reactions[0]['reactions']

        cheer_reaction = list(filter(lambda x: x['reactionType'] == 'cheer', journalist_reactions))
        cheer = cheer_reaction[0]['count'] if cheer_reaction else 0

    recommends_reactions = list(filter(lambda x: x['serviceId'] == 'NEWS_MAIN', contents))
    if recommends_reactions:
        recommends_reactions = recommends_reactions[0]['reactions']

        like_reaction = list(filter(lambda x: x['reactionType'] == 'like', recommends_reactions))
        recommends = like_reaction[0]['count'] if like_reaction else 0

    return total_reactions, recommends


async def get_comments_count(oid: str, aid: str) -> int:
    url = '{}/commonComment/listCount.nhn'.format(NAVER_NEWS_MOBILE_HOST)
    response = await post(url, data={'lang': 'ko', 'ticket': 'news', 'gnos': 'news{},{}'.format(oid, aid)})
    parsed = await response.json(content_type=None)

    return parsed['message']['result'][0]['count']


async def parse_ranking_read(uid: str, comments_count: int, ranking_read: str, oid: str, aid: str) -> Article:
    soup = BeautifulSoup(ranking_read, "lxml")

    reaction_layers = soup.select('div.u_likeit_list_module._reactionModule')
    like_layers = soup.select('div._reactionModule.u_likeit')

    # 27421
    journalist_id = reaction_layers[0]['data-cid']

    # NEWS
    news = like_layers[0]['data-sid']

    # NEWS_SUMMARY
    news_summary = like_layers[1]['data-sid']

    # ne_003_0009411453
    like_contents_id = 'ne_{}_{}'.format(oid, aid)

    # 003_0009411453
    oid_aid = '{}_{}'.format(oid, aid)

    # JOURNALIST_27421
    # channel_key = soup.select('a.subscribe.is_preparing._my_feed_btn')[0]['data-subscribechannelkey']

    if len(reaction_layers) == 1:

        # NEWS_MAIN
        news_main = reaction_layers[0]['data-sid']

        # NEWS[ne_003_0009411453]|NEWS_SUMMARY[003_0009411453]|NEWS_MAIN[ne_003_0009411453]
        q = '{}[{}]|{}[{}]|{}[{}]'.format(
            news, like_contents_id, news_summary, oid_aid, news_main, like_contents_id
        )

        reactions, recommends = await get_reactions_count(oid, aid, q)

    else:

        # period
        count_type = reaction_layers[0]['data-ccounttype']

        # JOURNALIST
        journalist = reaction_layers[0]['data-sid']

        # NEWS_MAIN
        news_main = reaction_layers[1]['data-sid']

        # NEWS[ne_003_0009411453]|NEWS_SUMMARY[003_0009411453]|JOURNALIST[24354(period)]|NEWS_MAIN[ne_003_0009411453]
        q = '{}[{}]|{}[{}]|{}[{}({})]|{}[{}]'.format(
            news, like_contents_id, news_summary, oid_aid, journalist, journalist_id, count_type,
            news_main, like_contents_id
        )

        reactions, recommends = await get_reactions_count(oid, aid, q)

    author = soup.select('.media_journalistcard_summary_name_text')
    if author:
        author = author[0].text
    else:
        author = None

    article = Article(
        uid=uid,
        title=soup.select("h2.media_end_head_headline")[0].text,
        content=soup.select("._news_article_body")[0].text.strip(),
        comments_count=comments_count,
        initialized_at=soup.select(".media_end_head_info_datestamp_time")[0].text,
        url='https://news.naver.com/main/read.nhn?oid={}&aid={}'.format(oid, aid),
        author=author,
        press=soup.select('img.media_end_head_top_logo_img')[0]['alt'],
        reactions=reactions,
        recommends=recommends
    )

    if len(soup.select(".media_end_head_info_datestamp_time")) > 1:
        article.finalized_at = soup.select(".media_end_head_info_datestamp_time")[1].text
    return article


async def get_ranking_list(category: int, date: str):
    response = await get('{}/rankingList.nhn?sid1={}&date={}'.format(NAVER_NEWS_MOBILE_HOST, category, date))
    soup = BeautifulSoup(await response.text(), 'lxml')

    titles = soup.find_all(class_="commonlist_tx_headline")

    logger.info('* Parsed Ranking list...')
    for i, title in enumerate(list(map(lambda x: x.text, titles))):
        logger.info('{}: {}'.format(i, title))

    links = soup.select("ul.commonlist > li > a")
    for link in list(map(lambda x: x.get('href'), links)):
        ranking_read_request = await get('{}{}'.format(NAVER_NEWS_MOBILE_HOST, link))
        ranking_read = await ranking_read_request.text()

        await client.hang_like_human()

        yield link, ranking_read


def parse_child_comment_list(child_comment_list: list) -> List[ChildComment]:
    try:
        return list(map(lambda comment:
                            ChildComment(
                                uid=comment['commentNo'],
                                parent_uid=comment['parentCommentNo'],
                                user_id=comment['userIdNo'],
                                username=comment['maskedUserId'],
                                nickname=comment['maskedUserName'],
                                content=comment['contents'],
                                like_count=comment['sympathyCount'],
                                dislike_count=comment['antipathyCount'],
                                registered_at=comment['regTime'],
                                modified_at=comment['modTime'],
                                exposed=comment['expose'],
                                deleted=comment['deleted'],
                            )
                        , child_comment_list))
    except:
        raise ParseResponseError


def parse_comment_list(comment_list: list) -> List[Comment]:
    try:
        return list(map(lambda comment:
                            Comment(
                                uid=comment['commentNo'],
                                user_id=comment['userIdNo'],
                                username=comment['maskedUserId'],
                                nickname=comment['maskedUserName'],
                                content=comment['contents'],
                                reply_count=comment['replyCount'],
                                like_count=comment['sympathyCount'],
                                dislike_count=comment['antipathyCount'],
                                registered_at=comment['regTime'],
                                modified_at=comment['modTime'],
                                exposed=comment['expose'],
                                deleted=comment['deleted'],
                            ), comment_list))
    except:
        raise ParseResponseError


async def _request_comment_list(category: int, date: str, url: str, oid: str, aid: str) -> tuple:
    request = await get(
        url,
        headers={
            'Referer': '{}/comment/list.nhn?gno=news{}%2c{}&aid={}&ntype=RANKING&oid={}&sid1={}&backUrl=%2frankingList.nhn%3fsid1%3d{}%26date%3d{}&light=off&date={}'.format(
                NAVER_NEWS_MOBILE_HOST, oid, aid, aid, oid, category, category, date, date
            )
        }
    )

    response = await request.text()
    parsed_response = parse_jquery_jsonp(response)

    has_next_page = int(parsed_response['result']['pageModel']['nextPage']) > 0
    return parsed_response, has_next_page


async def _get_comments(category: int, date: str, oid: str, aid: str,
                        template: str, parsed_response: dict) \
        -> List[Comment]:

    comment_list = parsed_response['result']['commentList']
    exposed_comment_list = list(filter(lambda comment: comment['expose'] == True, comment_list))

    parsed_comment_list = parse_comment_list(exposed_comment_list)
    has_replies = list(filter(lambda comment: (comment.reply_count or 0) > 0, parsed_comment_list))
    for comment in has_replies:
        child_comments = await get_child_comments(category, date, oid, aid, template, comment)
        comment.children = child_comments
    return parsed_comment_list


async def get_first_page_comments(category: int, date: str, oid: str, aid: str,
                                  template: str, save_callback)\
        -> Tuple[List[Comment], int]:
    logger.info('* Reading {},{}\'s comments first page...'.format(oid, aid))

    jquery = generate_jquery_jsonp_nonce()
    url = '{}/commentBox/cbox/web_neo_list_jsonp.json?ticket=news&templateId={}&pool=cbox5&_callback={}&lang=ko&country=&objectId=news{}%2C{}&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&page=1&initialize=true&userType=&useAltSort=true&replyPageSize=20&moveTo=&sort=new&includeAllStatus=true&_={}'.format(
        NAVER_API_HOST, template, jquery['jsonp_key'], oid, aid, jquery['nonce']
    )

    parsed_response, has_next_page = await _request_comment_list(category, date, url, oid, aid)
    total_pages = parsed_response['result']['pageModel']['totalPages']
    parsed_comment_list = await _get_comments(category, date, oid, aid, template, parsed_response)

    await save_callback(get_article_uid(oid, aid), parsed_comment_list)
    return parsed_comment_list, total_pages


async def get_more_page_comments(category: int, date: str, oid: str, aid: str, template: str,
                                 page: int, save_callback) \
        -> List[Comment]:
    logger.info('* Reading {},{}\'s comments {} page...'.format(oid, aid, page))
    jquery = generate_jquery_jsonp_nonce()
    url = '{}/commentBox/cbox/web_neo_list_jsonp.json?ticket=news&templateId={}&pool=cbox5&_callback={}&lang=ko&country=&objectId=news{}%2C{}&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&page={}&refresh=false&sort=NEW&includeAllStatus=true&_={}'.format(
            NAVER_API_HOST, template, jquery['jsonp_key'], oid, aid, page, jquery['nonce'])
    parsed_response, has_next_page = await _request_comment_list(category, date, url, oid, aid)

    parsed_comment_list = await _get_comments(category, date, oid, aid, template, parsed_response)
    await save_callback(get_article_uid(oid, aid), parsed_comment_list)

    await client.hang_like_human()

    return parsed_comment_list


async def get_first_page_child_comments(category: int, date: str, oid: str, aid: str, parent: str, template: str) \
        -> Tuple[List[ChildComment], int]:
    logger.info(
        '* Reading {},{}\'s {}\'s child comments first page ...'.format(oid, aid, parent))
    jquery = generate_jquery_jsonp_nonce()
    url = '{}/commentBox/cbox/web_neo_list_jsonp.json?ticket=news&templateId={}&pool=cbox5&_callback={}&lang=ko&country=&objectId=news{}%2C{}&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&parentCommentNo={}&page=1&userType=&includeAllStatus=true&moreType=next&_={}'.format(
            NAVER_API_HOST, template, jquery['jsonp_key'], oid, aid, parent, jquery['nonce'])
    parsed_child_response, has_child_next_page = await _request_comment_list(category, date, url, oid, aid)

    total_pages = parsed_child_response['result']['pageModel']['totalPages']

    child_comment_list = parsed_child_response['result']['commentList']
    exposed_child_comment_list = list(filter(lambda comment: comment['expose'] == True, child_comment_list))
    parsed_child_comment_list = parse_child_comment_list(exposed_child_comment_list)

    logger.debug('* Parsed child commentlist : {}'.format(parsed_child_comment_list))

    return parsed_child_comment_list, total_pages


async def get_more_page_child_comments(category: int, date: str, oid: str, aid: str, parent: str,
                                       template: str, page:int) -> List[ChildComment]:
    logger.info(
        '* Reading {},{}\'s {}\'s child comments {} page ...'.format(oid, aid, parent, page))

    jquery = generate_jquery_jsonp_nonce()
    url = '{}/commentBox/cbox/web_neo_list_jsonp.json?ticket=news&templateId={}&pool=cbox5&_callback={}&lang=ko&country=&objectId=news{}%2C{}&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&parentCommentNo={}&page={}&userType=&includeAllStatus=true&moreType=next&_={}'.format(
            NAVER_API_HOST, template, jquery['jsonp_key'], oid, aid, parent, page, jquery['nonce'])
    parsed_child_response, has_child_next_page = await _request_comment_list(category, date, url, oid, aid)

    child_comment_list = parsed_child_response['result']['commentList']
    exposed_child_comment_list = list(filter(lambda comment: comment['expose'] == True, child_comment_list))
    parsed_child_comment_list = parse_child_comment_list(exposed_child_comment_list)

    logger.debug('* Parsed child commentlist : {}'.format(parsed_child_comment_list))

    await client.hang_like_human()

    return parsed_child_comment_list


async def get_child_comments(category: int, date: str, oid: str, aid: str, template: str, comment: Comment)\
        -> List[ChildComment]:
    child_comments, child_end_page = await get_first_page_child_comments(category, date, oid, aid,
                                                                         comment.uid, template)

    await client.hang_like_human()

    futures = [asyncio.create_task(get_more_page_child_comments(category, date, oid, aid,
                                                                  comment.uid, template, page))
               for page in range(2, child_end_page)]
    parsed_child_comment_lists = await asyncio.gather(*futures)

    more_child_comments = [parsed_child_comments for parsed_child_comment_list in parsed_child_comment_lists
                           for parsed_child_comments in parsed_child_comment_list]
    child_comments.extend(more_child_comments)
    return child_comments


async def get_comments(category: int, date: str, oid: str, aid: str, template: str, save_callback):
    comments, end_page = await get_first_page_comments(category, date, oid, aid,
                                                       template, save_callback)

    await client.hang_like_human()

    futures = [asyncio.create_task(get_more_page_comments(category, date, oid, aid,
                               template, page, save_callback))
               for page in range(2, end_page)]
    parsed_comment_lists = await asyncio.gather(*futures)

    more_comments = [parsed_comments for parsed_comment_list in parsed_comment_lists
             for parsed_comments in parsed_comment_list]
    # comments.extend(more_comments)
    #
    # return comments
