# -*- coding: utf-8 -*-

import aiohttp
import random, logging, asyncio
from greatagain_parser_naver.parser.exceptions import RetryRequestError
from .proxy import get_proxies
from itertools import cycle
from tenacity import retry, wait_random_exponential, stop_after_attempt, before_log, retry_if_exception_type
from typing import Optional


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 15
REQUEST_TIMEOUT = 10
MIN_HUMAN_LKE_TIME = 2
MAX_HUMAN_LIKE_TIME = 3

class ProxyList(object):

    @property
    def origin(self):
        return self._proxies

    @origin.setter
    def origin(self, new_value):
        self._proxies = new_value
        self._circular = cycle(self._proxies)

    @property
    def empty(self):
        if hasattr(self, '_circular') and len(self._proxies) > 0:
            return False
        return True

    def next(self):
        if not hasattr(self, '_circular'):
            raise Exception('Please set `origin` first!')
        return next(self._circular)

    def remove(self, value):
        self._proxies.remove(value)
        self._circular = cycle(self._proxies)


PROXIES: ProxyList = ProxyList()

waiting_time: float = random.uniform(MIN_HUMAN_LKE_TIME, MAX_HUMAN_LIKE_TIME)
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

def get_random_user_agent() -> str:
    return random.choice(user_agent_strings)

session = aiohttp.ClientSession(
    headers={'User-Agent': get_random_user_agent()}
)

async def refresh_proxies(must_be_deleted_proxy: str):
    global PROXIES

    async with request_lock:
        try:
            PROXIES.remove(must_be_deleted_proxy)
        except KeyError as e:
            logging.warning(e)

        if PROXIES.empty:
            logging.error('Available proxies count is NOT satisfied!')
            PROXIES.origin = await get_proxies()


request_lock = asyncio.Lock()

@retry(wait=wait_random_exponential(multiplier=1, max=MAX_HUMAN_LIKE_TIME),
       stop=stop_after_attempt(MAX_RETRIES),
       before=before_log(logger, logging.DEBUG),
       retry=retry_if_exception_type(RetryRequestError))
async def request(method: str, url: str, headers: Optional[dict] = None,
                  **kwargs) -> aiohttp.ClientResponse:

    global PROXIES

    async with request_lock:
        if PROXIES.empty:
            logger.info('Searching proxy servers...')
            PROXIES.origin = await get_proxies()
            logger.info('The proxies will be used: {}'.format(PROXIES.origin))

        selected_proxy = PROXIES.next()

    if headers:
        headers.update({
            'User-Agent': get_random_user_agent()
        })

    try:
        response = await session.request(method, url,
                                         headers=headers,
                                         timeout=REQUEST_TIMEOUT,
                                         proxy=selected_proxy,
                                         **kwargs)

        await response.read()

        return response
    except (ConnectionError, aiohttp.ClientError,
            aiohttp.ClientSSLError, asyncio.TimeoutError) as e:
        logger.info('Occurred an ConnectionError {}!'.format(e))

        await refresh_proxies(selected_proxy)
        raise RetryRequestError

async def get(url: str, **kwargs) -> aiohttp.ClientResponse:
    return await request('GET', url, **kwargs)

async def post(url: str, **kwargs) -> aiohttp.ClientResponse:
    return await request('POST', url, **kwargs)

async def close():
    if not session.closed:
        await session.close()

async def hang_like_human(addition_time=0.0):
    waiting_time = random.uniform(MIN_HUMAN_LKE_TIME, MAX_HUMAN_LIKE_TIME)
    waiting_time += addition_time
    logger.debug('* Waiting for {} seconds...'.format(waiting_time))

    await asyncio.sleep(waiting_time)
