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

# 30초에 7개 요청 정도


import requests, random, time, json
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

MIN_HUMAN_LKE_TIME = 4.8
MAX_HUMAN_LIKE_TIME = 6.2

NAVER_NEWS_MOBILE_HOST = 'http://m.news.naver.com'
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

PROXIES = [
    '27.122.224.183:80',
    '211.108.3.235:816',
    '13.125.140.215:3128',
    '52.79.217.91:3128',
    '160.16.205.220:8080',
    '13.73.1.69:80'
]


category = 100
date = 20180128


def get_random_user_agent():
    # TODO DB로부터 가져오도록
    return 'Mozilla/5.0 (Linux; Android 6.0.1; SAMSUNG SM-G930T1 Build/MMB29M) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/4.0 Chrome/44.0.2403.133 Mobile Safari/537.36'


session = requests.Session()
session.headers.update({'User-Agent': get_random_user_agent()})
session.keep_alive = False


def get(url, **kwargs):
    selected_proxy = {
      'http': PROXIES[int(random.uniform(0, len(PROXIES)-1))],
      'https': PROXIES[int(random.uniform(0, len(PROXIES)-1))],
    }
    kwargs.update({'proxies': selected_proxy})
    print('| Try to connect {} with {}...'.format(url, selected_proxy))
    try:
        return session.get(url, **kwargs)
    except requests.exceptions.ConnectionError as e:
        print('Occurred an ConnectionError {}!'.format(e))
        hang_like_person(MAX_HUMAN_LIKE_TIME)
        return get(url, **kwargs)


waiting_time = random.uniform(MIN_HUMAN_LKE_TIME, MAX_HUMAN_LIKE_TIME)


def parse_ranking_read(ranking_read):
    soup = BeautifulSoup(ranking_read, "lxml")
    return {
        'title': soup.select("h2.media_end_head_headline")[0].text,
        'content': soup.select("._news_article_body")[0].text.strip(),
        'initialized_at': soup.select(".media_end_head_info_datestamp_time")[0].text,
        'finalized_at': soup.select(".media_end_head_info_datestamp_time")[1].text
    }


def get_ranking_list(category, date):
    response = get('{}/rankingList.nhn?sid1={}&date={}'.format(NAVER_NEWS_MOBILE_HOST, category, date))
    soup = BeautifulSoup(response.text, 'lxml')

    titles = soup.find_all(class_="commonlist_tx_headline")
    [print('{}: {}'.format(i, title)) for i, title in enumerate(list(map(lambda x: x.text, titles)))]

    links = soup.select("ul.commonlist > li > a")
    for link in list(map(lambda x: x.get('href'), links)):
        ranking_read = get('{}{}'.format(NAVER_NEWS_MOBILE_HOST, link))
        yield link, ranking_read


def generate_jquery_jsonp_nonce():
    expando = ('jQuery{}{}'.format('1.7', random.random())).replace('.', '')
    nonce = int(round(time.time() * 1000))
    return {
        'expando': expando,
        'nonce': nonce,
        'jsonp_key': '{}_{}'.format(expando, nonce-25)
    }


def parse_jquery_jsonp(response):
    parsed_response = response.text[response.text.index("(") + 1:response.text.rindex(")")]
    joined_response = " ".join(parsed_response.splitlines())
    return json.loads(joined_response)


def parse_comment_list(comment_list, is_children=False):
    if is_children:
        return list(map(lambda comment: {
            'id': comment['commentNo'],
            'parent': comment['parentCommentNo'],
            'user_id': comment['userIdNo'],
            'username': comment['maskedUserId'],
            'nickname': comment['maskedUserName'],
            'contents': comment['contents']
        }, comment_list))

    else:
        return list(map(lambda comment: {
            'id': comment['commentNo'],
            'user_id': comment['userIdNo'],
            'username': comment['maskedUserId'],
            'nickname': comment['maskedUserName'],
            'contents': comment['contents'],
            'replies': comment['replyCount']
        }, comment_list))


def request_comment_list(url, oid, aid):
    response = get(
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


def get_more_comments(oid, aid, page, template, last, first):
    jquery = generate_jquery_jsonp_nonce()
    url = '{}/commentBox/cbox/web_neo_list_jsonp.json?ticket=news&templateId={}&pool=cbox5&_callback={}&lang=ko&country=&objectId=news{}%2C{}&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&page={}&refresh=false&sort=FAVORITE&current={}&prev={}&includeAllStatus=true&_={}'.format(
            NAVER_API_HOST, template, jquery['jsonp_key'], oid, aid, page, last, first, jquery['nonce'])
    return request_comment_list(url, oid, aid)


def get_more_child_comments(oid, aid, parent, page, template, last):
    jquery = generate_jquery_jsonp_nonce()
    url = '{}/commentBox/cbox/web_neo_list_jsonp.json?ticket=news&templateId={}&pool=cbox5&_callback={}&lang=ko&country=&objectId=news{}%2C{}&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&parentCommentNo={}&page={}&userType=&includeAllStatus=true&moreType=next&current={}&_={}'.format(
            NAVER_API_HOST, template, jquery['jsonp_key'], oid, aid, parent, page, last, jquery['nonce'])
    return request_comment_list(url, oid, aid)


def get_child_comments(oid, aid, parent, template):
    jquery = generate_jquery_jsonp_nonce()
    url = '{}/commentBox/cbox/web_neo_list_jsonp.json?ticket=news&templateId={}&pool=cbox5&_callback={}&lang=ko&country=&objectId=news{}%2C{}&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&parentCommentNo={}&page=1&userType=&includeAllStatus=true&moreType=next&_={}'.format(
            NAVER_API_HOST, template, jquery['jsonp_key'], oid, aid, parent, jquery['nonce'])
    return request_comment_list(url, oid, aid)


def get_comments(oid, aid, category, template):
    jquery = generate_jquery_jsonp_nonce()
    page = 1
    url = '{}/commentBox/cbox/web_neo_list_jsonp.json?ticket=news&templateId={}&pool=cbox5&_callback={}&lang=ko&country=&objectId=news{}%2C{}&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&page={}&initialize=true&userType=&useAltSort=true&replyPageSize=20&moveTo=&sort=&includeAllStatus=true&_={}'.format(
            NAVER_API_HOST, template, jquery['jsonp_key'], oid, aid, page, jquery['nonce']
        )
    parsed_response, has_next_page = request_comment_list(url, oid, aid)
    comments = []
    current, prev = '', ''
    child_comments = []

    while True:
        if page > 1:
            parsed_response, has_next_page = get_more_comments(oid, aid, page, template,
                                                               current, prev)
        print('| Reading {},{}\'s comments {} page...'.format(oid, aid, page))
        parsed_comment_list = parse_comment_list(parsed_response['result']['commentList'])
        print('| Parsed commentlist : {}'.format(parsed_comment_list))
        has_replies = list(filter(lambda comment: int(comment['replies']) > 0, parsed_comment_list))
        for comment in has_replies:
            child_page = 1
            parsed_child_response, has_child_next_page = get_child_comments(oid, aid, comment['id'], template)
            child_current = ''
            while True:
                hang_like_person()
                if child_page > 1:
                    parsed_child_response, has_child_next_page = get_more_child_comments(oid, aid,
                                                     comment['id'], child_page, template, child_current)
                print('| Reading {},{}\'s {}\'s child comments {} page ...'.format(oid, aid, comment['id'], child_page))
                parsed_child_comment_list = parse_comment_list(parsed_child_response['result']['commentList'])
                print('| Parsed child commentlist : {}'.format(parsed_child_comment_list))
                child_comments.extend(parsed_child_comment_list)
                child_current = parsed_child_comment_list[-1]['id']
                if not has_child_next_page:
                    break
                child_page += 1
        comments.extend(parsed_comment_list)
        current, prev = parsed_comment_list[-1]['id'], parsed_comment_list[0]['id']
        if not has_next_page:
            break
        page += 1
        hang_like_person()
    return comments, child_comments


def hang_like_person(addition_time=0.0):
    waiting_time = random.uniform(MIN_HUMAN_LKE_TIME, MAX_HUMAN_LIKE_TIME)
    waiting_time += addition_time
    print('| Waiting for {} seconds...'.format(waiting_time))
    time.sleep(waiting_time)


if __name__ == '__main__':
    ranking_list = get_ranking_list(category, date)
    for link, ranking_read in ranking_list:
        news_article = parse_ranking_read(ranking_read.text)
        print('| Current rankingRead : {}'.format(news_article))
        hang_like_person()

        parsed_link = urlparse(link)
        link_parameters = parse_qs(parsed_link.query)

        comments, child_comments = get_comments(link_parameters['oid'][0], link_parameters['aid'][0], category,
                                                comment_templates[category])

        print('===================')
        print(news_article['title'])
        print({
            'comments': len(comments),
            'child_comments': len(child_comments),
        })
