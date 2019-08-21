# -*- coding: utf-8 -*-

import logging, re, os, asyncio, aiohttp
from selenium import webdriver
from typing import Optional


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'

TIMEOUT = 5
MIN_PROXY_COUNT = 3

PYTHONPATH = os.getenv("PYTHONPATH")
PHANTOM_JS_DRIVER_PATH = '{}/bin/phantomjs_mac'.format(PYTHONPATH)


async def from_proxy_lists():
    url = 'http://www.proxylists.net/jp_0.html'
    driver = webdriver.PhantomJS(PHANTOM_JS_DRIVER_PATH)
    driver.implicitly_wait(3)
    driver.get(url)

    proxies = ['http://{}:{}'.format(host, port) for (host, port) in re.findall('</script>(\d+\.\d+\.\d+\.\d+)\n<noscript>Please enable javascript</noscript></td><td>(\d+)</td></tr>', driver.page_source)]
    return proxies


async def from_hide_my_ip() -> list:
    """
    From "https://www.hide-my-ip.com/proxylist.shtml"
    :return:
    """
    url = 'https://www.hide-my-ip.com/proxylist.shtml'
    driver = webdriver.PhantomJS(PHANTOM_JS_DRIVER_PATH)
    driver.implicitly_wait(3)
    driver.get(url)

    try:
        data = driver.execute_script("return json;")

        # data = re.findall('"i":"(\d+\.\d+\.\d+\.\d+)","p":"(\d+)"', res.text)
        # proxies = ['{:s}:{:s}'.format(host, port) for (host, port) in data]

        proxies = ["{}://{}:{}".format(proxy['tp'], proxy['i'], proxy['p']) for proxy in data]

        return proxies
    except Exception as e:
        logging.error(e)

        return []


async def from_cyber_syndrome() -> list:
    """
    From "http://www.cybersyndrome.net/"
    :return:
    """
    url = 'http://www.cybersyndrome.net/pla6.html'

    proxies = []
    # res = requests.get(url)

    driver = webdriver.PhantomJS(PHANTOM_JS_DRIVER_PATH)
    driver.implicitly_wait(3)
    driver.get(url)

    # logging.debug(res.text)
    # proxies += re.findall('(\d+\.\d+\.\d+\.\d+:\d+)', res.text)

    proxies += ['http://{}'.format(ip) for ip in re.findall('(\d+\.\d+\.\d+\.\d+:\d+)', driver.page_source)]
    return proxies


async def from_free_proxy_list() -> list:
    """
    From "http://free-proxy-list.net/"
    :return:
    """
    urls = [
        # 'https://free-proxy-list.net/',
        'https://free-proxy-list.net/anonymous-proxy.html'
    ]
    proxies = []

    for url in urls:
        await asyncio.sleep(0.5)

        async with aiohttp.ClientSession() as session:
            res = await session.get(url)

            data = re.findall("<td>(\d+\.\d+\.\d+\.\d+)</td><td>(\d+)</td><td>(.*?)</td><td class='hm'>(.*?)</td><td>(.*?)</td><td class='hm'>(.*?)</td><td class='hx'>(.*?)</td><td class='hm'>(.*?)</td>",
                                await res.text()
                              )
            proxies += [
                'https://{:s}:{:s}'.format(host, port) if https == 'yes' else 'http://{:s}:{:s}'.format(host, port)
                for (host, port, code, country, anonymity, google, https, last_checked) in data
            ]

    return proxies


async def test_proxy(session: aiohttp.ClientSession, proxy: str) -> Optional[str]:
    # if not (proxy.startswith('http://') or proxy.startswith('https://')):
    #     proxy = 'http://{}'.format(proxy)

    headers = {
        'User-Agent': USER_AGENT
    }

    try:
        resp = await session.get(
            "https://www.naver.com",
            headers=headers,
            timeout=TIMEOUT,
            proxy=proxy,
            ssl=False
        )

        await resp.read()

        return proxy
    except Exception as e:
        logging.debug("Skip proxy {} by {}".format(proxy, e))
        return None


async def get_proxies() -> set:
    proxies = set()

    functions = [
        from_proxy_lists,
        from_hide_my_ip,
        from_cyber_syndrome,
        from_free_proxy_list,
    ]

    for func in functions:
        proxy_list = await func()

        logging.debug(proxy_list)

        async with aiohttp.ClientSession() as session:
            futures = [asyncio.create_task(test_proxy(session, proxy)) for proxy in proxy_list]
            results = await asyncio.gather(*futures)

            proxies.update(list(filter(lambda x: x is not None, results)))

    if len(proxies) < MIN_PROXY_COUNT:
        logging.error('Available proxies count is NOT satisfied!' 
                      'Current available is {}!'.format(len(proxies)))
        proxies = await get_proxies()
    return proxies
