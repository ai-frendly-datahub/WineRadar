"""Analyze Wine21 HTML structure to find correct selectors."""

import requests
from bs4 import BeautifulSoup


url = "https://www.wine21.com/11_news/reporter_news_list.html"

print("Fetching Wine21 page...")
response = requests.get(
    url,
    timeout=10,
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
)

print(f"Status: {response.status_code}")
print(f"Content length: {len(response.text)} bytes")

soup = BeautifulSoup(response.text, "html.parser")

# Try different selectors
selectors_to_try = [
    ('a[href*="reporter_news_view"]', "Links containing reporter_news_view"),
    ("div.board-list a", "Links in board-list div"),
    ("table.board-list a", "Links in board-list table"),
    ("tr a", "All links in table rows"),
    ('a[href*="news"]', "Links containing news"),
    ("div.list-item a", "Links in list-item div"),
    ("ul.news-list a", "Links in news-list ul"),
]

print("\nTrying different selectors:")
print("=" * 80)

for selector, description in selectors_to_try:
    elements = soup.select(selector)
    print(f"\n{description}")
    print(f"  Selector: {selector}")
    print(f"  Found: {len(elements)} elements")

    if elements:
        print("  First 3 matches:")
        for i, elem in enumerate(elements[:3], 1):
            href = elem.get("href", "")
            text = elem.get_text(strip=True)[:50]
            print(f"    {i}. {text}... -> {href}")

# Also check the page structure
print("\n\n" + "=" * 80)
print("Page structure analysis:")
print("=" * 80)

# Find all anchor tags
all_links = soup.find_all("a", href=True)
news_links = [a for a in all_links if "news" in a.get("href", "").lower()]

print(f"\nTotal links: {len(all_links)}")
print(f"Links with 'news' in href: {len(news_links)}")

if news_links:
    print("\nSample news links:")
    for i, link in enumerate(news_links[:5], 1):
        print(f"  {i}. Text: {link.get_text(strip=True)[:40]}")
        print(f"     Href: {link.get('href')}")
        print(f"     Parent: {link.parent.name if link.parent else 'None'}")
        print()
