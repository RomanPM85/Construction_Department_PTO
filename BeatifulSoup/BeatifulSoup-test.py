#!/usr/bin/python
# -*- coding: utf-8 -*-
# Современный скрапинг веб-сайтов с помощью Python "Райан Митчелл" 2021
from urllib.request import urlopen
from bs4 import BeautifulSoup
from urllib.error import HTTPError


def get_title(url):
    try:
        html = urlopen(url)
    except HTTPError as e:
        return None
    try:
        bs = BeautifulSoup(html.read(), 'html.parser')
        title = bs.body.h1
    except AttributeError as e:
        return None
    return title


if __name__ == "__main__":
    title = get_title('https://technical.city/ru/cpu/intel-rating')

    if title is None:
        print('title cold no be found')
    else:
        print(title)
