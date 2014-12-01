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

http://abuhijleh.net/2011/02/13/guide-scrape-multi-pages-content-with-scrapy/
http://bgrva.github.io/blog/2014/03/04/scrapy-after-tutorials-part-1/

"""


import scrapy
from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy import log
from alembic.items import DocItem

class Cdc_archive_spider(CrawlSpider):
    """
    Scrap each article listed in the media archive
    
    Use with `$> scrapy crawl cdc_media -a session_id=001 -s DEPTH_LIMIT=2 -o articles.json
    
    TODO: Scrapy alone cannot parse data rendered from jquery responses. We need a toolkit like Selenium to process the dynamic content and serve us the full page, as it would be in Firefox.
    
    See http://snipplr.com/view/66998/
    """

    name = "cdc_archive"
    session_id = -1 
    allowed_domains = ["cdc.gov"]
    
    start_urls = [
        "http://www.cdc.gov/media/archives.htm"
    ]
    
    rules = (Rule(  SgmlLinkExtractor(allow = ("",), restrict_xpaths=("//ul[contains(@id, 'pressrelease')]/li/a[contains(@class, 'item-title')]",)),
                    callback="parse_items", 
                    follow=True
             ),)
            
    
    def __init__(self, session_id=-1, *args, **kwargs):
        super(Cdc_Media_Spider, self).__init__(*args, **kwargs)
        self.session_id = session_id
        
    def parse_items(self, response):
        log.msg("Processing url: {0}".format(""+response.url), level=log.INFO)
        sel = Selector(response)
        items = []
        
        item = DocItem()
        item['session_id'] = self.session_id
        item['depth'] = response.meta["depth"]
        item['link'] = response.url 
        item['date'] = sel.xpath("//span[contains(@itemprop, 'dateModified')]").extract()
        
        title = sel.xpath("./h1/text()").extract()
        item['title'] = title
        log.msg("\tTitle: {0}".format(title), level=log.INFO)
        
        item['body'] = sel.css(".mSyndicate").xpath("./p/text()").extract()
        
        items.append(item)
        return items
            
class Cdc_article_spider(scrapy.Spider):
    """
    Parse an article page
    """

    name = "cdc_article"
    allowed_domains = ["cdc.gov"]
    
    start_urls = [
        "http://www.cdc.gov/media/releases/2014/p1126-adult-smoking.html",
        "http://www.cdc.gov/media/releases/2014/p1125-hiv-testing.html",
        "http://www.cdc.gov/media/releases/2014/p1120-excessive-drinking.html"
    ]
    
    def parse(self, response):
        log.msg("Processing url: {0}".format(""+response.url), level=log.INFO)
        sel = scrapy.Selector(response)
        items = []
        
        item = DocItem()
        
        item['session_id'] = self.session_id
        #item['depth'] = response.meta["depth"]
        item['link'] = response.url 
        item['date'] = sel.xpath("//span[contains(@itemprop, 'dateModified')]/text()").extract()
        
        title = sel.xpath("//h1/text()").extract()
        item['title'] = title
        log.msg("\tTitle: {0}".format(title), level=log.INFO)
        
        item['body'] = sel.css(".mSyndicate").xpath("./p/text()").extract()
        
        items.append(item)
        return items
    