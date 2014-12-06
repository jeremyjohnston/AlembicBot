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
from selenium import webdriver
from selenium.webdriver.remote import webelement
#from selenium import selenium
import time

class Cdc_archive_spider(scrapy.Spider):
    """
    Scrap each article listed in the media archive
    
    Use with `$> scrapy crawl cdc_archive -a session_id=001 -o articles.json
    
    TODO: Scrapy alone cannot parse data rendered from jquery responses. We need a toolkit like Selenium to process the dynamic content and serve us the full page, as it would be in Firefox.
    
    See http://snipplr.com/view/66998/
    """

    name = "cdc_archive"
    session_id = -1         #set by command line
    allowed_domains = ["cdc.gov"]
    
    topURL = "http://www.cdc.gov/media/archives.htm"
    
    #We'll fetch a list using selenium
    start_urls = []
    
    def __init__(self, session_id=-1, *args, **kwargs):
        super(Cdc_archive_spider, self).__init__(*args, **kwargs)
        self.session_id = session_id
        
        # Start up Selenium
        log.msg("starting selenium server...", level=log.INFO)
        self.verificationErrors = []
        #self.selenium=selenium("localhost",4444, "*chrome", "http://www.cdc.gov/media/") 
        self.driver = webdriver.Firefox()
        
        #start selenium with baseURL
        #self.selenium.start()
        #log.msg("selenium server started!", level=log.INFO)
        log.msg("selenium driver started!", level=log.INFO)
        
        # print "Name: ", self.selenium.__class__.__name__
        # print "Class: ",self.selenium.__class__
        # print "Base: ", self.selenium.__class__.__bases__
        # print "Dict: ", self.selenium.__dict__
        
        
        # Open top url 
        #self.selenium.open(self.topURL)
        self.driver.get(self.topURL)
        time.sleep(5) # Wait for javascript to load
        
        # and get list of URLs
        xpath_getlinks = "//ul[contains(@id, 'pressrelease')]/li/a[contains(@class, 'item-title')]"
        #matches = 0 
        #matches = self.selenium.get_xpath_count(xpath_getlinks)
        #print "Hits: ", matches
        #sites = self.selenium.get_text(xpath_getlinks)
        
        # see http://stackoverflow.com/questions/17975471/selenium-with-scrapy-for-dynamic-page
        linkElements = self.driver.find_elements_by_xpath(xpath_getlinks) #WebElement list
        
        articles = []
        for e in linkElements:
            articles.append(e.get_attribute('href'))
        
        log.msg("Found articles: \n{0}".format(articles), level=log.INFO)
        print "Found {0} articles: \n{1}".format(len(articles), articles) 
        
        # Add articles links to start_urls 
        Cdc_archive_spider.start_urls.extend(articles)
        
        # Now scrapy will call parse() on each article 
        
    def __del__(self):
        #self.selenium.stop()
        log.msg("Verification Errors: \n{0}".format(self.verificationErrors), level=log.INFO)
        log.msg("DONE", level=log.INFO)
        self.driver.close()
        print "DONE"
        #super.__del__(self) -->#Causes exception that says scrapy.Spider has no __del__() ?
    
    def parse(self, response):
        """
        Called automatically by scrapy on every start_url
        """
        print "Processing: ", ""+response.url
        log.msg("Processing url: {0}".format(""+response.url), level=log.INFO)
        sel = scrapy.Selector(response)
        items = []
        
        item = DocItem()
        item['session_id'] = self.session_id
        
        item['link'] = response.url 
        item['date'] = sel.xpath("//span[contains(@itemprop, 'dateModified')]/text()").extract()
        
        title = sel.xpath("(//h1)[1]/text()").extract()
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
        
        title = sel.xpath("(//h1)[1]/text()").extract()
        item['title'] = title
        log.msg("\tTitle: {0}".format(title), level=log.INFO)
        
        item['body'] = sel.css(".mSyndicate").xpath("./p/text()").extract()
        
        items.append(item)
        return items

            