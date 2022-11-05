import json
import time
from scrapy import Spider
from playwright.sync_api import sync_playwright
import re

# TODO-URGENT: Do something about JavaScript loaded webpages

spaces_re = re.compile(r'\s+')


class ScrollableSpider(Spider):
    name = 'scrollable'

    def __init__(self,
                 base_url=None,
                 article_locator_query=None,
                 *args, **kwargs):
        self.start_urls = ["data:,"]  # avoid using the default Scrapy downloader
        super(ScrollableSpider, self).__init__(*args, **kwargs)
        self.base_url = base_url
        self.article_locator_query = article_locator_query

    def parse(self, response, **kwargs):
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context()

            page = context.new_page()
            page.goto(self.base_url)

            # Scroll down, while there's still new content loaded
            old_count = 0
            while True:
                page.mouse.wheel(0, 15000)
                time.sleep(2)

                count = page.locator(self.article_locator_query).count()
                print(f"count={count}")
                if old_count == count:
                    break
                old_count = count
                time.sleep(1)

            article_locator = page.locator(self.article_locator_query)
            count = article_locator.count()
            if count != old_count:
                print('---------------- ODD RESULT ----------------')
            for i in range(count):
                article = article_locator.nth(i)
                yield {
                    'title': article.text_content(),
                    'url': article.get_attribute("href"),
                }

            browser.close()
            context.close()
