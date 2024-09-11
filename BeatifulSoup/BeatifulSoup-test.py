#!/usr/bin/python
# -*- coding: utf-8 -*-
# Современный скрапинг веб-сайтов с помощью Python "Райан Митчелл" 2021
from urllib.request import urlopen
from bs4 import BeautifulSoup
from urllib.error import HTTPError


if __name__ == "__main__":
    # title = get_title('https://technical.city/ru/cpu/intel-rating')
    html = urlopen('http://www.pythonscraping.com/pages/page3.html')
    bs = BeautifulSoup(html.read(), 'html.parser')
    # for child in bs.find('table', {'id': 'giftList'}).children:
    #     print(child)
    for sibling in bs.find('table', {'id': 'giftList'}).tr.next_siblings:
        print(sibling)
