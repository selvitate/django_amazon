from scrapy.crawler import CrawlerProcess
from scrapy import signals
from twisted.internet import reactor
from scrapy.crawler import Crawler
from scrapy.settings import Settings
from scrapy.utils.project import get_project_settings

from amazon_2.spiders.amazon_search_result import AmazonSearchResultSpider
from amazon_2.spiders.product_page import ProductPageSpider


class Launch:

    def __init__(self, scr_type='search_result'):
        if scr_type == 'search_result':
            self.launch = self.__launch_search_result
        elif scr_type == 'page_scrapper':
            self.launch = self.__launch_page_scrapper
        else:
            print('Error with name!')
            self.launch = None

    def __launch_search_result(self, keywords=None, max_pages=None):
        process = CrawlerProcess(get_project_settings())
        process.crawl(AmazonSearchResultSpider, keywords=keywords, max_pages=max_pages)
        process.start()

    def __launch_page_scrapper(self, keyword=None, with_rewiews=None, image_manage=None):
        process = CrawlerProcess(get_project_settings())
        process.crawl(ProductPageSpider, keyword=keyword, with_rewiews=with_rewiews, image_manage=image_manage)
        process.start()

if __name__ == '__main__':
    launch = Launch(scr_type='page_scrapper')
    launch.launch('laptop')