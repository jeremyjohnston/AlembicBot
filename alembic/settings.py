# -*- coding: utf-8 -*-

# Scrapy settings for alembic project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'alembic'
SPIDER_MODULES = ['alembic.spiders']
NEWSPIDER_MODULE = 'alembic.spiders'
DOWNLOAD_DELAY = 2
DEPTH_LIMIT = 2
LOG_FILE = 'scrapy.log'
LOG_LEVEL='INFO'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'AlembicBot/0.1 (+http://utdallas.edu/~jpj054000/bot.htm)'
