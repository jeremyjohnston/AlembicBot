# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class DmozItem(scrapy.Item):
    title = scrapy.Field()
    link = scrapy.Field()
    desc = scrapy.Field()

class DocItem(scrapy.Item):
    session_id = scrapy.Field()
    depth = scrapy.Field()
    title = scrapy.Field() 
    link = scrapy.Field()
    date = scrapy.Field()
    body = scrapy.Field()