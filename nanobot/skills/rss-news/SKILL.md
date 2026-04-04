---
name: rss-news
description: Fetch and summarize the latest news from RSS feeds with automatic clean text extraction and a built-in 1-hour cache.
metadata: {"nanobot":{"emoji":"📰","requires":{"bins":["python"]}}}
---

# RSS News

This skill fetches the latest news from RSS feeds.

It features:
- **Clean text extraction**: Automatically strips out messy HTML tags and symbols to present a clean summary.
- **Built-in cache**: News articles are cached for 1 hour to prevent excessive API requests.
- **Configurable RSS source**: By default, it retrieves news from the BBC News RSS feed. However, it can be configured in the bot's configuration file.

## Configuration

You can configure the base URL for the RSS feed (e.g., to point to an RSSHub instance) in the bot's configuration file under `tools.rss_news.rsshub_base_url`.

Example configuration:
```yaml
tools:
  rss_news:
    rsshub_base_url: "https://feeds.bbci.co.uk/news/rss.xml"
```

## Usage

You can use the included `fetch_news.py` script to get the latest news. It will print the parsed and cleaned text of the most recent news articles.

```bash
python scripts/fetch_news.py
```
