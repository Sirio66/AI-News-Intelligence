import feedparser
import requests
from bs4 import BeautifulSoup


def fetch_full_article(url):
    try:
        response = requests.get(url, timeout=10)

        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")

        text = " ".join([p.get_text() for p in paragraphs])

        return text.strip()

    except Exception as e:
        print(f"Error fetching article: {e}")
        return ""


def fetch_rss_articles(rss_url):
    import feedparser

    feed = feedparser.parse(rss_url)
    articles = []

    for entry in feed.entries:
        articles.append({
            "title": entry.title,
            "url": entry.link,
            "content": entry.get("summary", "")  
        })

    return articles