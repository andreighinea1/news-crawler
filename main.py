from scrapy import signals, Spider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.signalmanager import dispatcher


class BlogSpider(Spider):
    name = 'blog_spider'

    def __init__(self, *args, **kwargs):
        super(BlogSpider, self).__init__(*args, **kwargs)
        self.start_urls = ['https://www.zyte.com/blog/']

    def parse(self, response, **kwargs):
        for title in response.css('.oxy-post-title'):
            yield {'title': title.css('::text').get()}

        for next_page in response.css('a.next'):
            yield response.follow(next_page, self.parse)


def spider_results():
    results = []

    def crawler_results(signal, sender, item, response, spider):
        results.append(item)

    dispatcher.connect(crawler_results, signal=signals.item_scraped)

    process = CrawlerProcess(get_project_settings())
    process.crawl(BlogSpider)
    process.start()  # the script will block here until the crawling is finished
    return results


if __name__ == '__main__':
    print(spider_results())
