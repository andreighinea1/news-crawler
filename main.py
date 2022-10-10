import json
import time
from collections import defaultdict

from scrapy import signals, Spider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.signalmanager import dispatcher

from playwright.sync_api import sync_playwright


class BlogSpider(Spider):
    name = 'blog_spider'

    def __init__(self, base_url=None, article_locator_query=None, next_locator_query=None, *args, **kwargs):
        self.base_url = base_url
        self.start_urls = [base_url]
        super(BlogSpider, self).__init__(*args, **kwargs)
        self.article_locator_query = article_locator_query
        self.next_locator_query = next_locator_query

    def parse(self, response, **kwargs):
        for title in response.css(self.article_locator_query):
            yield {
                'title': title.css('::text').get(),
                'url': title.attrib['href'],
            }

        for next_url in response.css(self.next_locator_query):
            yield response.follow(next_url, self.parse)


class ScrollableSpider(Spider):
    name = 'scrollable_spider'

    def __init__(self, base_url=None, article_locator_query=None, *args, **kwargs):
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

                # if count >= 30:
                #     break

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


def get_results(*add_to_process_functions):
    # Init results
    temp_results = defaultdict(list)

    def crawler_results(signal, sender, item, response, spider):
        temp_results[spider.base_url].append(item)
    dispatcher.connect(crawler_results, signal=signals.item_scraped)

    # Init and start process
    process = CrawlerProcess(get_project_settings())
    for add_to_process_func in add_to_process_functions:
        add_to_process_func(process)
    process.start()  # the script will block here until the crawling is finished

    # Preprocess results
    results = {
        source: {
            "Cnt": len(res_list),
            "results": res_list
        }
        for source, res_list in temp_results.items()
    }
    del temp_results

    # Save and return results
    with open("results.json", "w") as fout:
        json.dump(results, fout, indent=4)
    return results


def add_bitdefender_to_process(process):
    process.crawl(ScrollableSpider,
                  base_url="https://www.bitdefender.com/blog/labs/",
                  article_locator_query=".article-thumb__link")


def add_zyte_results_to_process(process):
    process.crawl(BlogSpider,
                  base_url="https://www.zyte.com/blog/",
                  article_locator_query=".oxy-post-title",
                  next_locator_query="a.next")


if __name__ == '__main__':
    get_results(
        add_zyte_results_to_process,
        add_bitdefender_to_process,
    )
