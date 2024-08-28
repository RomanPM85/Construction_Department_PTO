from urllib.request import urlopen
from bs4 import BeautifulSoup
from urllib.error import HTTPError

try:
    html = urlopen('https://technical.city/ru/cpu/intel-rating')
    bs = BeautifulSoup(html.read(), 'html.parser')
    print(bs.h1)
except HTTPError as error:
    print(error)
