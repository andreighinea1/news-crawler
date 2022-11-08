from abc import ABC
from typing import Dict

import scrapy_splash
from scrapy import Spider
from scrapy_splash import SplashRequest

from news_crawler import constants


class BaseSpider(Spider, ABC):
    @staticmethod
    def follow_dynamically(response, parse_func, *, href=None, url=None, meta=None):
        if not url:
            url = response.urljoin(href)

        return SplashRequest(url, parse_func,
                             args={
                                 'wait': 0.5,
                                 'timeout': 90,
                                 'images': 0,
                                 'resource_timeout': 20,
                             },
                             # endpoint='render.json',  # optional; default is render.html
                             meta=meta
                             )

    @staticmethod
    def get_url_to_title(a, response) -> tuple[str, str]:
        url: str = a.attrib['href']
        if not url.startswith('http'):
            url = response.urljoin(url)

        title = a.css('::text').get()
        if not title:
            if a.css('img').get():
                title = constants.IMG_PLACEHOLDER
        return url, title
