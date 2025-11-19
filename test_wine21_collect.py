# -*- coding: utf-8 -*-
"""Test Wine21 collection with updated config."""

import requests
from bs4 import BeautifulSoup
import re

url = "https://www.wine21.com/11_news/news_list.html"

print(f"Fetching {url}...")
response = requests.get(url, timeout=10, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

print(f"Status: {response.status_code}")
soup = BeautifulSoup(response.text, 'html.parser')

# Find JavaScript news links
js_links = soup.select("a[href*='goNewsViewDirect']")
print(f"\nFound {len(js_links)} JavaScript links")

if js_links:
    print("\nFirst 5 articles:")
    for i, link in enumerate(js_links[:5], 1):
        text = link.get_text(strip=True)
        href = link.get('href', '')

        # Extract article ID from JavaScript
        match = re.search(r'goNewsViewDirect\((\d+)\)', href)
        article_id = match.group(1) if match else None

        # Build article URL
        article_url = f"https://www.wine21.com/11_news/news_view.html?news_no={article_id}" if article_id else None

        print(f"\n{i}. {text}")
        print(f"   Original href: {href}")
        print(f"   Article ID: {article_id}")
        print(f"   Article URL: {article_url}")

# Also try direct links
direct_links = soup.select("a[href*='news_view']")
print(f"\n\nDirect news_view links: {len(direct_links)}")

if direct_links:
    print("Sample direct links:")
    for link in direct_links[:3]:
        print(f"  {link.get('href')}")
