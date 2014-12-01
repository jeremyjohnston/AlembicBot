import scrapy

from alembic.items import DmozItem

"""
Few things to do.

Lots of things to make the crawling more efficient but ethical, i.e. not get banned

* We need to add crawling rules to follow links on the page and crawl them as well.
* Select the right data for our item (test xpaths using firefox and xpath checker)
* Item pipelines to filter content
* Store content in form for rest of program.

Rest of program will then rank each document's text, and build an index from them.

A good reference:
http://doc.scrapy.org/en/latest/topics/practices.html#bans

"""

class DmozSpider(scrapy.Spider):
    name = "dmoz"
    
    # Delay to not trigger throttling
    download_delay = 2 
    
    allowed_domains = ["dmoz.org"]
    start_urls = [
        "http://www.dmoz.org/Computers/Programming/Languages/Python/Books/",
        "http://www.dmoz.org/Computers/Programming/Languages/Python/Resources/"
    ]

    def parse(self, response):
        for sel in response.xpath('//ul/li'):
            item = DmozItem()
            item['title'] = sel.xpath('a/text()').extract()
            item['link'] = sel.xpath('a/@href').extract()
            item['desc'] = sel.xpath('text()').extract()
            yield item
            