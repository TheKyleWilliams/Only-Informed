import feedparser
from app import db
from app.models import Article
from datetime import datetime
from dateutil import parser as date_parser
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
        try:
            feed = feedparser.parse(feed_url)

            # check for parsing errors
            if feed.bozo:
                print(f"Error parsing feed: {feed_url}")
                continue # skips to next feed

            # cycles through individual articles
            for entry in feed.entries:
                # extract relevant data from RSS feed structure
                title = entry.title
                link = entry.link
                summary = entry.summary if 'summary' in entry else ''

                # handle different date formats
                if 'published' in entry:
                    date_str = entry.published
                elif 'updated' in entry:
                    date_str = entry.updated
                else:
                    date_str = datetime.now(datetime.timezone.utc).isoformat() # current time

                try:
                    published_date = date_parser.parse(date_str)
                except (ValueError, TypeError) as e:
                    print(f"Date parsing error for entry '{title}': {e}")
                    published_date = datetime.now(datetime.timezone.utc)

                # check if article already exists in database
                existing_article = Article.query.filter_by(title=title).first()

                # if new article
                if not existing_article:
                    # create new article object
                    article = Article(
                        title = title,
                        content = summary,
                        source = link,
                        date_posted = published_date
                    )

                    # add to database session, then commit to save
                    db.session.add(article)
                    db.session.commit()
                    print(f"Added article: {title}")
                else:
                    print(f"Article already exists: {title}")

        except Exception as e:
            print(f"Exception occured while fetching feed {feed_url}: {e}")

if __name__ == '__main__':
    from app import app
    with app.app_context():
        fetch_articles()