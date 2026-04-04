import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the root directory to sys.path to easily import the script
# or use importlib.util.spec_from_file_location
import importlib.util

spec = importlib.util.spec_from_file_location("fetch_news", "nanobot/skills/rss-news/scripts/fetch_news.py")
fetch_news = importlib.util.module_from_spec(spec)
sys.modules["fetch_news"] = fetch_news
spec.loader.exec_module(fetch_news)

class TestFetchNewsParsing:
    def test_clean_html(self):
        html_text = "<p>This is a <b>test</b>.</p> &amp; it works!"
        cleaned = fetch_news.clean_html(html_text)
        assert cleaned == "This is a test. & it works!"

        empty_cleaned = fetch_news.clean_html(None)
        assert empty_cleaned == ""

        messy_text = "  <div>   Some \n text  </div>  "
        assert fetch_news.clean_html(messy_text) == "Some text"

    def test_parse_rss(self):
        sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test News</title>
                <item>
                    <title>Test Article 1</title>
                    <description>&lt;p&gt;This is the &lt;b&gt;description&lt;/b&gt;.&lt;/p&gt;</description>
                    <link>http://example.com/1</link>
                    <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
                </item>
                <item>
                    <title>No description item</title>
                </item>
            </channel>
        </rss>
        """

        items = fetch_news.parse_rss(sample_xml)
        assert len(items) == 2

        # Test full item
        assert items[0]['title'] == "Test Article 1"
        assert items[0]['description'] == "This is the description."
        assert items[0]['link'] == "http://example.com/1"
        assert items[0]['pubDate'] == "Mon, 01 Jan 2024 12:00:00 GMT"

        # Test item missing fields
        assert items[1]['title'] == "No description item"
        assert items[1]['description'] == ""
        assert items[1]['link'] == ""
        assert items[1]['pubDate'] == ""

    @patch('fetch_news.httpx.get')
    def test_fetch_rss_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<rss></rss>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_news.fetch_rss("http://example.com/rss")
        assert result == "<rss></rss>"
        mock_get.assert_called_once()

    @patch('fetch_news.httpx.get')
    def test_fetch_rss_failure(self, mock_get):
        from httpx import HTTPError
        mock_get.side_effect = HTTPError("Connection failed")

        result = fetch_news.fetch_rss("http://example.com/rss")
        assert result.startswith("Error fetching news:")

    @patch('fetch_news.fetch_rss')
    @patch('fetch_news.get_cached_news')
    @patch('fetch_news.save_news_cache')
    def test_get_news_cache_hit(self, mock_save_cache, mock_get_cached_news, mock_fetch_rss):
        # Cache hit
        mock_get_cached_news.return_value = [{"title": "Cached Title"}]

        result = fetch_news.get_news("http://example.com/rss")
        assert result == [{"title": "Cached Title"}]
        mock_fetch_rss.assert_not_called()
        mock_save_cache.assert_not_called()

    @patch('fetch_news.fetch_rss')
    @patch('fetch_news.get_cached_news')
    @patch('fetch_news.save_news_cache')
    def test_get_news_cache_miss(self, mock_save_cache, mock_get_cached_news, mock_fetch_rss):
        # Cache miss
        mock_get_cached_news.return_value = None
        mock_fetch_rss.return_value = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0"><channel><item><title>Fresh Title</title></item></channel></rss>"""

        result = fetch_news.get_news("http://example.com/rss")
        assert len(result) == 1
        assert result[0]['title'] == "Fresh Title"
        mock_fetch_rss.assert_called_once()
        mock_save_cache.assert_called_once()

    @patch('fetch_news.fetch_rss')
    @patch('fetch_news.get_cached_news')
    def test_get_news_xml_error(self, mock_get_cached_news, mock_fetch_rss):
        # Invalid XML
        mock_get_cached_news.return_value = None
        mock_fetch_rss.return_value = "This is not valid XML"

        result = fetch_news.get_news("http://example.com/rss")
        assert isinstance(result, str)
        assert result.startswith("Error parsing RSS XML:")
