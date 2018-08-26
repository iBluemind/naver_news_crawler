# -*- coding: utf-8 -*-

import requests, random, time, logging, asyncio, functools
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, ProxyError, ReadTimeout
from requests import Request
# from config import PROXIES
from .proxy import get_proxies
from itertools import cycle
from greatagain_parser_naver import loop


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


MAX_RETRIES = 10
REQUEST_TIMEOUT = 15


ERROR_LIMIT = 10


MIN_HUMAN_LKE_TIME = 1.5
MAX_HUMAN_LIKE_TIME = 1.5

waiting_time = random.uniform(MIN_HUMAN_LKE_TIME, MAX_HUMAN_LIKE_TIME)


user_agent_strings = [
'Mozilla/5.0 (Linux; Android 6.0.1; SAMSUNG SM-G930T1 Build/MMB29M) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/4.0 Chrome/44.0.2403.133 Mobile Safari/537.36',
'Mozilla/5.0 (Linux; Android 7.0; SM-G892A Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/60.0.3112.107 Mobile Safari/537.36 NAVER(inapp; search; 590; 8.8.3)',
'Mozilla/5.0 (Linux; Android 7.0; SM-G930VC Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/58.0.3029.83 Mobile Safari/537.36 NAVER(inapp; search; 590; 8.8.3)',
'Mozilla/5.0 (Linux; Android 6.0.1; SM-G935S Build/MMB29K; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/55.0.2883.91 Mobile Safari/537.36 NAVER(inapp; search; 590; 8.8.3)',
'Mozilla/5.0 (iPhone; CPU iPhone OS 11_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15F79 NAVER(inapp; search; 590; 8.8.5; 8)',
'Mozilla/5.0 (iPhone; CPU iPhone OS 11_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.0 Mobile/15E148 Safari/604.1',
'Mozilla/5.0 (Linux; Android 6.0.1; SM-G920V Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36 NAVER(inapp; search; 590; 8.8.3)',
'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Mobile/15A372 NAVER(inapp; search; 590; 8.8.5; 8)',
'Mozilla/5.0 (iPhone9,3; U; CPU iPhone OS 10_0_1 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/14A403 Safari/602.1',
'Mozilla/5.0 (iPhone9,3; U; CPU iPhone OS 10_0_1 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Mobile/14A403 NAVER(inapp; search; 590; 8.8.5; 8)',
'Mozilla/5.0 (iPhone9,4; U; CPU iPhone OS 10_0_1 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/14A403 Safari/602.1',
'Mozilla/5.0 (iPhone9,4; U; CPU iPhone OS 10_0_1 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Mobile/14A403 NAVER(inapp; search; 590; 8.8.5; 8)',
'Mozilla/5.0 (Apple-iPhone7C2/1202.466; U; CPU like Mac OS X; ko) AppleWebKit/420+ (KHTML, like Gecko) Version/3.0 Mobile/1A543 Safari/419.3',
'Mozilla/5.0 (Apple-iPhone7C2/1202.466; U; CPU like Mac OS X; ko) AppleWebKit/420+ (KHTML, like Gecko) Mobile/1A543 NAVER(inapp; search; 590; 8.8.5; 8)'
]


def get_random_user_agent():
    return random.choice(user_agent_strings)


session = requests.Session()
session.headers.update({'User-Agent': get_random_user_agent()})
session.mount('https://', HTTPAdapter(max_retries=MAX_RETRIES))
session.mount('http://', HTTPAdapter(max_retries=MAX_RETRIES))


proxies = loop.run_until_complete(get_proxies())
PROXIES = cycle(proxies)


def refresh_proxies(must_be_deleted_proxy):
    global proxies, PROXIES
    try:
        proxies.remove(must_be_deleted_proxy)
    except KeyError as e:
        logging.warning(e)
        pass
    from .proxy import MIN_PROXY_COUNT
    if len(proxies) < MIN_PROXY_COUNT:
        proxies = loop.run_until_complete(get_proxies())
    PROXIES = cycle(proxies)


def pick_proxies():
    return next(PROXIES)


def make_request(method, url, **kwargs):
    request = Request(method, url, **kwargs)
    prepped = session.prepare_request(request)
    prepped.headers['User-Agent'] = get_random_user_agent()
    return prepped


async def request(prepped_request):
    selected_proxy = pick_proxies()

    try:
        response = await loop.run_in_executor(None, functools.partial(session.send,
                                                                      prepped_request,
                                                                      proxies={
                                                                            'http': selected_proxy,
                                                                            'https': selected_proxy,
                                                                        },
                                                                      timeout=REQUEST_TIMEOUT))
        # hang_like_human()
        return response
    except (ConnectionError, ProxyError, ReadTimeout) as e:
        logger.info('Occurred an ConnectionError {}!'.format(e))
        # hang_like_human(MAX_HUMAN_LIKE_TIME)

        refresh_proxies(selected_proxy)
        return await request(prepped_request)


async def get(url, **kwargs):
    prepped = make_request('GET', url, **kwargs)
    return await request(prepped)


async def post(url, **kwargs):
    prepped = make_request('POST', url, **kwargs)
    return await request(prepped)


def hang_like_human(addition_time=0.0):
    waiting_time = random.uniform(MIN_HUMAN_LKE_TIME, MAX_HUMAN_LIKE_TIME)
    waiting_time += addition_time
    logger.info('| Waiting for {} seconds...'.format(waiting_time))
    time.sleep(waiting_time)
