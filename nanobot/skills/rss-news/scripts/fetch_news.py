import os
import json
import time
import httpx
import xml.etree.ElementTree as ET
import re

def clean_html(raw_html: str) -> str:
    """Removes HTML tags and strange symbols from text."""
    if not raw_html:
        return ""
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', raw_html)
    # Decode some common HTML entities
    clean_text = clean_text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
    # Clean up whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def parse_rss(xml_content: str):
    """Parses RSS XML and returns a list of news items."""
    root = ET.fromstring(xml_content)
    items = []

    # Handle standard RSS 2.0
    for item in root.findall('.//item'):
        title_elem = item.find('title')
        desc_elem = item.find('description')
        link_elem = item.find('link')
        pubdate_elem = item.find('pubDate')

        title = title_elem.text if title_elem is not None else "No Title"
        description = clean_html(desc_elem.text) if desc_elem is not None else ""
        link = link_elem.text if link_elem is not None else ""
        pubdate = pubdate_elem.text if pubdate_elem is not None else ""

        items.append({
            'title': clean_html(title),
            'description': description,
            'link': link,
            'pubDate': pubdate
        })

    return items

def fetch_rss(url: str) -> str:
    """Fetches RSS feed content from URL."""
    try:
        # User-Agent is sometimes required by feeds like BBC to not block requests
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; nanobot/1.0; +https://github.com/nanobot-ai/nanobot)'}
        response = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as e:
        return f"Error fetching news: {e}"

import hashlib
from pathlib import Path

def get_cache_path(url: str) -> Path:
    """Generates a safe cache file path based on URL."""
    # Use MD5 to generate a unique filename for the URL
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    # Cache directory at ~/.../cache/rss-news/ or /tmp/rss-news-cache/
    cache_dir = Path.home() / '.cache' / 'nanobot-rss-news'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{url_hash}.json"

def get_cached_news(url: str, max_age_seconds: int = 3600):
    """Retrieves news from cache if valid."""
    cache_file = get_cache_path(url)
    if not cache_file.exists():
        return None

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check expiration
        cache_time = data.get('timestamp', 0)
        if time.time() - cache_time > max_age_seconds:
            return None

        return data.get('items')
    except (json.JSONDecodeError, IOError):
        return None

def save_news_cache(url: str, items: list):
    """Saves news items to cache."""
    cache_file = get_cache_path(url)
    try:
        data = {
            'timestamp': time.time(),
            'items': items
        }
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except IOError:
        pass # Silently fail cache writes

def get_news(url: str):
    """Fetches and parses news from URL, using cache if available."""
    cached_items = get_cached_news(url)
    if cached_items is not None:
        return cached_items

    xml_content = fetch_rss(url)
    if xml_content.startswith("Error"):
        return xml_content

    try:
        items = parse_rss(xml_content)
        if items:
            save_news_cache(url, items)
        return items
    except ET.ParseError as e:
        return f"Error parsing RSS XML: {e}"

def main():
    try:
        from nanobot.config import load_config
        config = load_config()
        base_url = config.tools.rss_news.rsshub_base_url
    except Exception:
        # Fallback if config isn't available
        base_url = "https://feeds.bbci.co.uk/news/rss.xml"

    print(f"Fetching news from: {base_url}\n")
    news_items = get_news(base_url)

    if isinstance(news_items, str):
        print(news_items) # Error message
    elif not news_items:
        print("No news found.")
    else:
        for i, item in enumerate(news_items[:10], 1):
            print(f"{i}. {item['title']}")
            print(f"   {item['description']}")
            print(f"   Link: {item['link']}")
            print(f"   Published: {item['pubDate']}")
            print()

if __name__ == "__main__":
    main()
