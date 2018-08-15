# -*- coding: utf-8 -*-

import requests, random, time, logging
from requests.adapters import HTTPAdapter
from config import PROXIES


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


MIN_HUMAN_LKE_TIME = 2.2
MAX_HUMAN_LIKE_TIME = 4.6

waiting_time = random.uniform(MIN_HUMAN_LKE_TIME, MAX_HUMAN_LIKE_TIME)


def get_random_user_agent():
    # TODO DB로부터 가져오도록
    return 'Mozilla/5.0 (Linux; Android 6.0.1; SAMSUNG SM-G930T1 Build/MMB29M) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/4.0 Chrome/44.0.2403.133 Mobile Safari/537.36'


session = requests.Session()
session.headers.update({'User-Agent': get_random_user_agent()})
session.keep_alive = False
session.mount('https://', HTTPAdapter(max_retries=10))
session.mount('http://', HTTPAdapter(max_retries=10))


def get(url, **kwargs):
    selected_proxy = {
      'http': PROXIES[int(random.uniform(0, len(PROXIES)-1))],
      'https': PROXIES[int(random.uniform(0, len(PROXIES)-1))],
    }
    kwargs.update({'proxies': selected_proxy})
    logger.info('| Try to GET {} with {}...'.format(url, selected_proxy))
    try:
        request = session.get(url, **kwargs)
        hang_like_person()
        return request
    except requests.exceptions.ConnectionError as e:
        logger.info('Occurred an ConnectionError {}!'.format(e))
        hang_like_person(MAX_HUMAN_LIKE_TIME)
        return get(url, **kwargs)


def post(url, **kwargs):
    selected_proxy = {
      'http': PROXIES[int(random.uniform(0, len(PROXIES)-1))],
      'https': PROXIES[int(random.uniform(0, len(PROXIES)-1))],
    }
    kwargs.update({'proxies': selected_proxy})
    logger.info('| Try to POST {} with {}...'.format(url, selected_proxy))
    try:
        request = session.post(url, **kwargs)
        hang_like_person()
        return request
    except requests.exceptions.ConnectionError as e:
        logger.info('Occurred an ConnectionError {}!'.format(e))
        hang_like_person(MAX_HUMAN_LIKE_TIME)
        return post(url, **kwargs)


def hang_like_person(addition_time=0.0):
    waiting_time = random.uniform(MIN_HUMAN_LKE_TIME, MAX_HUMAN_LIKE_TIME)
    waiting_time += addition_time
    logger.info('| Waiting for {} seconds...'.format(waiting_time))
    time.sleep(waiting_time)
