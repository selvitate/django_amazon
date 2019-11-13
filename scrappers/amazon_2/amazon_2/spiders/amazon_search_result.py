# -*- coding: utf-8 -*-
import scrapy
from scrapy.utils.project import get_project_settings
from amazon_2.items import AmazonProductItem
import random
import logging

class AmazonSearchResultSpider(scrapy.Spider):

    name = 'amazon_search_result'
    allowed_domains = ['amazon.in']
    base_url = 'https://www.amazon.in'

    start_urls = [
        'https://www.example.com'
    ]
    custom_settings = {
        'ITEM_PIPELINES': {
            'amazon_2.pipelines.AmazonSearchResultPipeline': 300,
            'amazon_2.pipelines.AmazonProductDump': 301,
        },
        # this is delays between requests(in sec).
        # If you want get faster, you can change it, but it is on your own risk

        # Write now i know, that you can make delay to 0.5 sec!! So it will be faster
        'DOWNLOAD_DELAY': 0.5,
    }
    settings = get_project_settings()

    default_stars = {
        'one_star': 1,
        'two_star': 2,
        'three_star': 3,
        'four_star': 4,
        'five_star': 5,
    }

    def __init__(self, *args, **kwargs):
        super(AmazonSearchResultSpider, self).__init__(*args, **kwargs)
        logging.warning(kwargs)

        keywords = kwargs.get('keywords', None)
        if keywords:
            self.keywords = keywords.split(',')
        else:
            self.keywords = []
        self.image_manage = 'link'
        self.max_pages = kwargs.get('pages', None)

    def parse(self, response):
        # logging.warning(self.keywords)
        # next we create the request fo our keyword
        for keyword in self.keywords:
            searching_url = 'https://www.amazon.in/s?k={}'
            url = searching_url.format(keyword)
            yield scrapy.Request(url=url, callback=self.parse_page_result, meta={
                'page': 1,
                'keyword': keyword
            })

    def parse_page_result(self, response):
        # check the captcha
        error_text = response.xpath('//p[@class="a-last"]/text()').get()
        if error_text == "Sorry, we just need to make sure you're not a robot. " \
                         "For best results, please make sure your browser is accepting cookies.":
            # time.sleep(15)
            user_agent = random.choice(self.settings.get('USER_AGENTS'))
            yield scrapy.Request(url=response.url, callback=self.parse_page_result,
                                 headers={'User-Agent': user_agent},
                                 dont_filter=True, meta=response.meta)
        else:
            item = AmazonProductItem()
            # we take all results from page
            blocks = response.css('.s-result-item')
            page = response.meta.get('page')
            # passing all blocks, get the info, and pass request to the product page
            for block in blocks:
                asin = block.xpath('@data-asin').get()
                if not asin:
                    continue
                item['asin'] = asin
                item['title'] = block.css('.a-color-base.a-text-normal::text').get()
                item['rewiev_count'] = block.css('.a-link-normal .a-size-base::text').get()
                if block.css('.a-spacing-micro .a-color-secondary').get():
                    item['sponsored'] = True
                    item['sponsored_page'] = page
                    item['sponsored_position'] = block.xpath('@data-index').get()
                else:
                    item['sponsored'] = False
                    item['sponsored_page'] = None
                    item['sponsored_position'] = None
                if block.css('.s-prime .a-icon-medium').get():
                    item['prime'] = True
                else:
                    item['prime'] = False
                if block.css('.s-align-children-center .s-align-children-center+ .a-row span').get():
                    item['free_delivery'] = True
                else:
                    item['free_delivery'] = False
                url = self.base_url + block.css('.a-size-mini a::attr(href)').get()
                item['url'] = url
                item['price'] = block.css('.a-price-whole::text').get()
                item['stars'] = block.css('.a-size-small .a-icon-alt::text').get()
                item['keyword'] = response.meta.get('keyword')
                item['scrapper'] = 'amazon_search_result'
                yield item
            # pagination
            if response.xpath('//li[@class="a-last"]').get() and page != self.max_pages:
                page += 1
                url = 'https://www.amazon.in/s?k={}&page={}'.format(response.meta.get('keyword'), page)
                yield scrapy.Request(url=url, callback=self.parse_page_result, meta={
                    'keyword': response.meta.get('keyword'),
                    'page': page
                })

