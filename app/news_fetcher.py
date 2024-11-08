import feedparser
from app import db
from app.models import Article
from datetime import datetime
import ssl

# bypass SSL certificate errors, if any
ssl._create_default_https_context = ssl._create_unverified_context

def fetch_articles():
    # list of RSS feed URLs
    feeds = [
        'https://feeds.bbci.co.uk/news/world/rss.xml'
    ]

    # loop through RSS feeds
    for feed_url in feeds:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            
