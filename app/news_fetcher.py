import feedparser
from app import db
from app.models import Article
from datetime import datetime, timezone
from dateutil import parser as date_parser
from newspaper import Article as NewsArticle
import ssl

# Bypass SSL certificate errors, if any
ssl._create_default_https_context = ssl._create_unverified_context

def fetch_articles():
    # List of RSS feed URLs
    feeds = [
        'https://feeds.bbci.co.uk/news/world/rss.xml'
    ]

    # Loop through RSS feeds
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)

            # Check for parsing errors
            if feed.bozo:
                print(f"Error parsing feed: {feed_url}")
                continue  # Skips to next feed

            # Cycle through individual articles
            for entry in feed.entries:
                # Extract relevant data from RSS feed structure
                title = entry.title
                link = entry.link
                # summary = entry.summary if 'summary' in entry else ''

                # Handle different date formats
                if 'published' in entry:
                    date_str = entry.published
                elif 'updated' in entry:
                    date_str = entry.updated
                else:
                    date_str = datetime.now(timezone.utc).isoformat()  # Current time

                try:
                    published_date = date_parser.parse(date_str)
                except (ValueError, TypeError) as e:
                    print(f"Date parsing error for entry '{title}': {e}")
                    published_date = datetime.now(timezone.utc)

                # Check if article already exists in database
                existing_article = Article.query.filter_by(title=title).first()

                # If new article
                if not existing_article:
                    article_text, top_image = get_full_article_content(link, title)  # Pass both link and title

                    # Create new article object
                    article = Article(
                        title=title,
                        content=article_text,
                        source=link,
                        date_posted=published_date,
                        image_url=top_image  # Save the main image URL
                    )

                    # Add to database session, then commit to save
                    db.session.add(article)
                    db.session.commit()
                    print(f"Added article: {title}")
                else:
                    print(f"Article already exists: {title}")

        except Exception as e:
            print(f"Exception occurred while fetching feed {feed_url}: {e}")

# Grab entire article content and main image URL
def get_full_article_content(url, title):
    article = NewsArticle(url)
    article.download()
    article.parse()
    content = article.text

    # Remove the title from the content if present
    if content.startswith(title):
        content = content[len(title):].strip()

    # Remove lines that are likely to be image captions
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove lines that start with 'Watch:' or contain specific keywords
        if not line.lower().startswith('watch:') and not 'prison' in line.lower():
            cleaned_lines.append(line)
    cleaned_content = '\n'.join(cleaned_lines)

    return cleaned_content, article.top_image

# Allows news_fetcher to be run manually as a module
if __name__ == '__main__':
    from app import app

    # Ensures that app operations will run despite Flask not being 'run'
    with app.app_context(): 
        fetch_articles()