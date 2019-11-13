# -*- coding: utf-8 -*-
import scrapy
import mysql.connector
from scrapy.utils.project import get_project_settings
from inline_requests import inline_requests
import random
from amazon_2.items import AmazonProductItem


class ProductPageSpider(scrapy.Spider):
    name = 'amazon_product_page'
    allowed_domains = ['amazon.in']
    start_urls = [
        'https://www.example.com'
    ]
    settings = get_project_settings()
    base_url = 'https://www.amazon.in'
    default_stars = {
        'one_star': 1,
        'two_star': 2,
        'three_star': 3,
        'four_star': 4,
        'five_star': 5,
    }

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

    def __init__(self, *args, **kwargs):
        super(ProductPageSpider, self).__init__(*args, **kwargs)
        self.keyword = kwargs.get('keyword', None)
        self.with_rewiews = kwargs.get('reviews', None)
        self.image_manage = kwargs.get('image', 'link')

    def start_requests(self):
        db_settings = get_project_settings().get('DB_SETTINGS')

        self.conn = mysql.connector.connect(
            host=db_settings.get('host'),
            user=db_settings.get('user'),
            passwd=db_settings.get('passwd'),
            database=db_settings.get('database')
        )
        self.curr = self.conn.cursor()

        if self.keyword:
            query = "SELECT * FROM product WHERE status = ('new') AND keyword = (%s)"
            self.curr.execute(query, (self.keyword,))
        else:
            self.curr.execute("""
                SELECT * FROM product
                WHERE status = ('new')
            """)
        links = self.curr.fetchall()
        for link in links:
            url = link[4]
            yield scrapy.Request(url=url, callback=self.parse, meta={'link': link})


    def get_review(self, response):
        # get reviews
        item = []
        blocks = response.css('.review-text-content span')[:5]
        dates = response.css('#cm_cr-review_list .review-date')[:5]
        for block, date in zip(blocks, dates):
            rewiev = {
                'date': date.css('::text').get(),
                'text': ' '.join(block.css('::text').getall())
            }
            item.append(rewiev)
        return item

    @inline_requests
    def parse(self, response):
        # check the captcha
        data = response.meta.get('link')
        error_text = response.xpath('//p[@class="a-last"]/text()').get()
        if error_text == "Sorry, we just need to make sure you're not a robot. " \
                         "For best results, please make sure your browser is accepting cookies.":
            # time.sleep(15)
            user_agent = random.choice(self.settings.get('USER_AGENTS'))
            yield scrapy.Request(url=response.url, callback=self.parse,
                                 headers={'User-Agent': user_agent},
                                 dont_filter=True, meta=response.meta)
        else:
            item = AmazonProductItem()
            item['scrapper'] = 'product_page'
            item['asin'] = response.meta.get('link')[1]
            item['title'] = response.meta.get('link')[2]
            item['description'] = response.xpath('//*[@id="feature-bullets"]//li//text()').getall()
            if not item['description']:
                item['description'] = response.xpath('//div[@id="bookDescription_feature_div"]/noscript/div/text()').getall()
            if not item['description']:
                item['description'] = response.xpath('//div[@id="productDescription_feature_div"]//p/text()').getall()
            item['top_100'] = False
            tables = response.css('.attrG')
            if tables:
                for table in tables:
                    attr = table.xpath('//td[contains(text(), "Amazon Bestsellers Rank")]/following::node()[1]'
                                                   '//text()').getall()
                    if attr:
                        item['product_rank'] = attr
                        break
            else:
                item['product_rank'] = response.xpath('//li[@id="SalesRank"]/text()').getall()
                item['product_rank'].extend(response.xpath('//li[@id="SalesRank"]/ul//text()').getall())
            item['seller'] = response.xpath('//a[@id="sellerProfileTriggerId"]/text()').get()
            if not item['seller']:
                item['seller'] = 'Amazon'
            # get the links of reviews page and send requests
            table = response.xpath('//td[@class="aok-nowrap"]//@href').getall()
            item['top5_rewiews'] = []
            if self.with_rewiews:
                for idx, elem in enumerate(table):
                    for default_star in self.default_stars:
                        if default_star in elem:
                            url_star = default_star
                    url = self.base_url + elem
                    res = yield scrapy.Request(url=url)
                    item['top5_rewiews'].append(
                        {'star':self.default_stars[url_star],
                         'data': self.get_review(res)}
                    )
            item['image'] = response.xpath('//div[@id="imageBlock_feature_div"]/script').get()
            yield item