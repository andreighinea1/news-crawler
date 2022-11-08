import json
import time
import re
from collections import defaultdict

from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.http import Response
from scrapy.utils.project import get_project_settings
from scrapy.signalmanager import dispatcher

from news_crawler import misc
from news_crawler.misc import sort_dict_by_keys
from news_crawler.spiders.blog_spider import BlogSpider

# TODO-URGENT: Do something about JavaScript loaded webpages
# docker pull scrapinghub/splash
# docker run -p 8050:8050 scrapinghub/splash

# TODO: Use https://doc.scrapy.org/en/latest/topics/autothrottle.html


def get_results(*add_to_process_functions):
    # Init results
    temp_results = defaultdict(dict)

    def crawler_results(signal, sender, item, response, spider):
        url = item.pop('url')
        temp_results[spider.base_url][url] = {  # Unique by url
            **item
        }

    dispatcher.connect(crawler_results, signal=signals.item_scraped)

    # Init and start process
    process = CrawlerProcess(get_project_settings())
    for add_to_process_func in add_to_process_functions:
        add_to_process_func(process)
    process.start()  # the script will block here until the crawling is finished

    # Preprocess results
    results = {
        source: {
            "Cnt": len(res_dict),
            "results": misc.sort_dict_by_keys(res_dict)
        }
        for source, res_dict in temp_results.items()
    }
    results = sort_dict_by_keys(results)
    del temp_results

    # Save and return results
    with open("results.json", "w") as fout:
        json.dump(results, fout, indent=4)
    return results


# def __add_bitdefender_scrollable_to_process(process):
#     process.crawl(ScrollableSpider,
#                   base_url="https://www.bitdefender.com/blog/labs/",
#                   article_locator_query=".article-thumb__link")


def add_bitdefender_to_process(process):
    process.crawl(BlogSpider,
                  base_url="https://www.bitdefender.com/blog/labs/tag/antimalware-research/",
                  article_locator_query=".article-thumb__link",
                  content_locator_query_list="div.col-lg-8 > div.single-post__content.mb-5",
                  next_locator_query="a.button-view-all.button-view-all--tags.d-inline-block.mx-2",
                  next_contains_text='›')


def add_zyte_results_to_process(process):
    process.crawl(BlogSpider,
                  base_url="https://www.zyte.com/blog/",
                  article_locator_query=".oxy-post-title",
                  content_locator_query_list="div#div_block-73-674.ct-div-block > div#blog-body.ct-text-block",
                  next_locator_query="a.next")


def add_tomsguide_results_to_process(process):
    process.crawl(BlogSpider,
                  base_url="https://www.tomsguide.com/news/archive/",
                  article_locator_query="li.day-article > a[href]",
                  content_locator_query_list="section.content-wrapper > div#article-body",
                  next_locator_query="ul.smaller.indented.basic-list > li > ul > li > a")


# def add_custom_tomsguide_results_to_process(process):
#     process.crawl(BlogSpider,
#                   base_url="https://www.tomsguide.com/news/archive/2008/11",
#                   article_locator_query="li.day-article > a[href]",
#                   content_locator_query_list="section.content-wrapper > div#article-body",
#                   next_locator_query="ul.smaller.indented.basic-list > li > ul > li > a")


if __name__ == '__main__':
    get_results(
        add_bitdefender_to_process,
        add_tomsguide_results_to_process,  # TODO: Remove text from 'aside' tags
        add_zyte_results_to_process,
    )
