import json
import time
from scrapy import Spider
from scrapy.http import Response
import re

# TODO-URGENT: Do something about JavaScript loaded webpages

spaces_re = re.compile(r'\s+')


class BlogSpider(Spider):
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
        self.content_locator_query_list = content_locator_query_list
        self.next_locator_query = next_locator_query
        self.next_contains_text = next_contains_text

    def content_parse_elem(self, response: Response, content_locator_query_list, **kwargs):
        content = ' '.join([
            ' '.join(response.css(clq).css('::text').getall())
            for clq in content_locator_query_list
        ])
        content = spaces_re.sub(' ', content).strip()

        res = {
            'title': response.meta.get('title', None),
            'url': response.meta.get('url', None),
            'content': content
        }
        return res

    def content_parse(self, response, **kwargs):
        if not isinstance(self.content_locator_query_list, list):
            self.content_locator_query_list = [self.content_locator_query_list]
        return self.content_parse_elem(response=response,
                                       content_locator_query_list=self.content_locator_query_list,
                                       **kwargs)

    def parse(self, response, **kwargs):
        for x in response.css(self.article_locator_query):
            url = x.attrib['href']
            yield response.follow(url, self.content_parse,
                                  meta={
                                      'title': x.css('::text').get().strip(),
                                      'url': url,
                                  })

        for next_url in response.css(self.next_locator_query):
            if (not self.next_contains_text or
                    next_url.css('::text').get() == self.next_contains_text):
                yield response.follow(next_url, self.parse)
