# -*- coding: utf-8 -*-

import requests, logging, time, re, os
from selenium import webdriver
from requests.exceptions import ConnectTimeout, ProxyError, SSLError, ConnectionError


TIMEOUT = 5
MIN_PROXY_COUNT = 2


# def from_proxy_lists():
#     url = 'http://www.proxylists.net/jp_0_ext.html'


def from_hide_my_ip():
    """
    From "https://www.hide-my-ip.com/proxylist.shtml"
    :return:
    """
    url = 'https://www.hide-my-ip.com/proxylist.shtml'

    current_working_directory = os.getcwd()
    driver = webdriver.PhantomJS('{}/bin/phantomjs_mac'.format(current_working_directory))

    driver.implicitly_wait(3)
    driver.get(url)

    proxies = driver.execute_script("return json;")
    logging.debug(proxies)

    # data = re.findall('"i":"(\d+\.\d+\.\d+\.\d+)","p":"(\d+)"', res.text)
    # proxies = ['{:s}:{:s}'.format(host, port) for (host, port) in data]
    return proxies


def from_cyber_syndrome():
    """
    From "http://www.cybersyndrome.net/"
    :return:
    """
    url = 'http://www.cybersyndrome.net/pla6.html'

    proxies = []
    res = requests.get(url)
    proxies += re.findall('(\d+\.\d+\.\d+\.\d+:\d+)', res.text)
    return proxies


def from_free_proxy_list():
    """
    From "http://free-proxy-list.net/"
    :return:
    """
    urls = [
        'https://free-proxy-list.net/',
        'https://free-proxy-list.net/anonymous-proxy.html'
    ]
    proxies = []

    for url in urls:
        time.sleep(0.5)
        res = requests.get(url)
        data = re.findall('<tr><td>(\d+\.\d+\.\d+\.\d+)</td><td>(\d+)</td>', res.text)
        proxies += ['{:s}:{:s}'.format(host, port) for (host, port) in data]
    return proxies


def get_proxies():
    proxies = set()

    functions = [
        from_cyber_syndrome,
        from_free_proxy_list,
    ]

    for func in functions:
        proxy_list = func()
        logging.debug(proxy_list)

        for proxy in proxy_list:
            try:
                requests.get("https://google.com", timeout=TIMEOUT, proxies={"http": proxy, "https": proxy})
                proxies.add(proxy)
            except (ConnectTimeout, ProxyError, SSLError, ConnectionError) as e:
                logging.info("Skip proxy {} by {}".format(proxy, e))

    if len(proxies) < MIN_PROXY_COUNT:
        logging.error("Available proxies count is NOT satisfied! Current available is {}!".format(len(proxies)))
        proxies = get_proxies()
    return proxies
