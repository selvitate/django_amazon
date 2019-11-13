# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class AmazonProductItem(scrapy.Item):
    title = scrapy.Field()
    description = scrapy.Field()
    url = scrapy.Field()
    price = scrapy.Field()
    image = scrapy.Field()
    stars = scrapy.Field()
    seller = scrapy.Field()
    seller_rating = scrapy.Field()
    rewiev_count = scrapy.Field()
    scrapper = scrapy.Field()
    prime = scrapy.Field()
    is_topseller = scrapy.Field()
    is_amazonchoice = scrapy.Field()
    free_delivery = scrapy.Field()
    product_rank = scrapy.Field()
    top5_rewiews = scrapy.Field()
    keyword = scrapy.Field()
    sponsored = scrapy.Field()
    sponsored_page = scrapy.Field()
    sponsored_position = scrapy.Field()
    asin = scrapy.Field()
    top_100 = scrapy.Field()
    category = scrapy.Field()