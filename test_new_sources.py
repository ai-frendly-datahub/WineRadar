# -*- coding: utf-8 -*-
"""Test new RSS sources to verify they work."""

import requests
import feedparser
from collections import defaultdict

# New sources to test
NEW_RSS_SOURCES = [
    ("Jancis Robinson", "https://www.jancisrobinson.com/articles/feed"),
    ("Wine & Spirits Magazine", "https://www.winemag.com/feed/"),
    ("Wine-Searcher", "https://www.wine-searcher.com/rss.lml"),
    ("Vinetur", "https://www.vinetur.com/feed/"),
    ("The World's 50 Best", "https://www.theworlds50best.com/stories/feed"),
    ("Vinogusto", "https://www.vinogusto.com/feed/"),
    ("Wine Magazine SA", "https://www.winemag.co.za/feed/"),
    ("Austin Wine Journal", "https://www.austinwinejournal.com/feed/"),
    ("Meininger's", "https://www.meininger.de/en/rss.xml"),
]

print("=" * 70)
print("Testing New RSS Sources")
print("=" * 70)

results = defaultdict(list)

for name, url in NEW_RSS_SOURCES:
    print(f"\n[{name}]")
    print(f"  URL: {url}")

    try:
        # Test HTTP request
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()

        # Parse feed
        feed = feedparser.parse(response.content)

        if feed.bozo:
            print(f"  Status: WARNING - Feed has parsing issues")
            print(f"  Bozo exception: {feed.bozo_exception}")
            results['warning'].append(name)
        else:
            print(f"  Status: OK")

        entry_count = len(feed.entries)
        print(f"  Entries: {entry_count}")

        if entry_count > 0:
            latest = feed.entries[0]
            title = latest.get('title', 'N/A')[:60]
            print(f"  Latest: {title}...")
            results['success'].append(name)
        else:
            print(f"  No entries found")
            results['empty'].append(name)

    except requests.exceptions.RequestException as e:
        print(f"  Status: FAILED")
        print(f"  Error: {e}")
        results['failed'].append(name)
    except Exception as e:
        print(f"  Status: ERROR")
        print(f"  Error: {e}")
        results['error'].append(name)

# Summary
print("\n" + "=" * 70)
print("Summary")
print("=" * 70)
print(f"Success: {len(results['success'])}")
for name in results['success']:
    print(f"  - {name}")

if results['warning']:
    print(f"\nWarnings: {len(results['warning'])}")
    for name in results['warning']:
        print(f"  - {name}")

if results['empty']:
    print(f"\nEmpty feeds: {len(results['empty'])}")
    for name in results['empty']:
        print(f"  - {name}")

if results['failed']:
    print(f"\nFailed: {len(results['failed'])}")
    for name in results['failed']:
        print(f"  - {name}")

if results['error']:
    print(f"\nErrors: {len(results['error'])}")
    for name in results['error']:
        print(f"  - {name}")

print("\n" + "=" * 70)
print(f"Total tested: {len(NEW_RSS_SOURCES)}")
print(f"Working: {len(results['success']) + len(results['warning'])}")
print(f"Success rate: {((len(results['success']) + len(results['warning'])) / len(NEW_RSS_SOURCES)) * 100:.1f}%")
print("=" * 70)
