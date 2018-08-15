# -*- coding: utf-8 -*-

import random, time, json


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
