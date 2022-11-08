import json
import time
from scrapy import Spider
from scrapy.http import Response
import re

from news_crawler.spiders.base_spider import BaseSpider

# TODO-URGENT: Do something about JavaScript loaded webpages

spaces_re = re.compile(r'\s+')


class BlogSpider(BaseSpider):
    name = 'blog'

    def __init__(self,
                 base_url=None,
                 key=None,
                 article_locator_query=None,
                 content_locator_query_list=None,
                 next_locator_query=None,
                 next_contains_text=None,
                 *args, **kwargs):
        self.base_url = base_url
        self.start_urls = [base_url]
        self.key = key
        super(BlogSpider, self).__init__(*args, **kwargs)
        self.article_locator_query = article_locator_query
        self.next_locator_query = next_locator_query
        self.next_contains_text = next_contains_text

        if not isinstance(content_locator_query_list, list):
            content_locator_query_list = [content_locator_query_list]
        self.content_locator_query_list = content_locator_query_list

    def content_parse_elem(self, response: Response, **kwargs):
        content = ' '.join([
            ' '.join(response.css(clq + ' :not(script)').css('::text').getall())
            for clq in self.content_locator_query_list
        ])
        content = content.replace("(opens in new tab)", '')
        content = spaces_re.sub(' ', content).strip()

        contained_urls = dict([
            self.get_url_to_title(a, response)
            for clq in self.content_locator_query_list
            for a in response.css(clq + ' a[href]')
            # if not print(a.get())
        ])

        res = {
            'title': response.meta.get('title', None),
            'url': response.meta.get('url', None),
            'content': content,
            'contained_urls': contained_urls
        }
        return res

    def content_parse(self, response, **kwargs):
        return self.content_parse_elem(response=response,
                                       **kwargs)

    def parse(self, response, **kwargs):
        for a in response.css(self.article_locator_query):
            href = a.attrib['href']
            url = response.urljoin(href)
            meta = {
                'title': a.css('::text').get().strip(),
                'url': url,
            }

            if 'FOLLOW_STATIC' not in kwargs:
                yield self.follow_dynamically(response, self.content_parse, url=url,
                                              meta=meta)
            else:
                yield response.follow(href, self.content_parse,
                                      meta=meta)

        for next_href in response.css(self.next_locator_query):
            if (not self.next_contains_text or
                    next_href.css('::text').get() == self.next_contains_text):
                yield response.follow(next_href, self.parse)
                # yield self.follow_dynamically(response, next_href, self.parse)
