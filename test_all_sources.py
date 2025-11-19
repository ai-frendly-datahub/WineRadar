# -*- coding: utf-8 -*-
"""Comprehensive test for all active and new sources."""

import requests
import feedparser
from collections import defaultdict
from bs4 import BeautifulSoup

# All sources to test
RSS_SOURCES = [
    # New sources added
    ("WINE WHAT!?", "https://wine-what.jp/feed/", "NEW"),
    ("Enolife", "https://enolife.com.ar/feed/", "NEW"),

    # Previously working
    ("Decanter", "https://www.decanter.com/feed/", "EXISTING"),
    ("The Drinks Business", "https://www.thedrinksbusiness.com/feed/", "EXISTING"),
    ("Terre de Vins", "https://www.terredevins.com/feed", "EXISTING"),
    ("Gambero Rosso", "https://www.gamberorosso.it/feed/", "EXISTING"),
    ("Wine Enthusiast", "https://www.wineenthusiast.com/feed/", "EXISTING"),
    ("Vinography", "https://www.vinography.com/feed", "EXISTING"),

    # Recently added - need verification
    ("Wine & Spirits Magazine", "https://www.winemag.com/feed/", "VERIFY"),
    ("Vinogusto", "https://www.vinogusto.com/feed/", "VERIFY"),
    ("Wine Magazine SA", "https://www.winemag.co.za/feed/", "VERIFY"),
]

HTML_SOURCES = [
    ("Wines of China", "https://www.winesofchina.com/news", "NEW"),
    ("Japan Wine", "https://japan-wine.jp/news/", "NEW"),
    ("Wine21", "https://www.wine21.com/11_news/reporter_news_list.html", "EXISTING"),
]

# Alternative sources to explore for disabled ones
ALTERNATIVE_RSS_SOURCES = [
    # For Jancis Robinson (404)
    ("Jancis Robinson Purple Pages", "https://www.jancisrobinson.com/learn/purple-pages/feed"),

    # For Wine-Searcher (403) - try alternative
    ("Wine-Searcher News", "https://www.wine-searcher.com/rss-news.lml"),

    # For Vinetur (404) - Spanish alternatives
    ("Vinetur Alternative", "https://vinetur.com/feed"),
    ("ACE Vinos", "https://www.acenologia.com/feed/"),

    # For Meininger's (403) - German alternatives
    ("WeinPlus", "https://www.wein.plus/en/rss/"),

    # Additional quality sources
    ("Wine-Searcher Magazine", "https://www.wine-searcher.com/rss-magazine.lml"),
    ("Robert Parker", "https://www.robertparker.com/feed"),
    ("VinePair", "https://vinepair.com/wine-blog/feed/"),
    ("Punch", "https://punchdrink.com/feed/"),
    ("Guild of Sommeliers", "https://www.guildsomm.com/public_content/feed"),
    ("WineBerserkers", "https://www.wineberserkers.com/forum/feed.php"),
    ("Tim Atkin MW", "https://www.timatkin.com/feed/"),
]

print("=" * 80)
print("WineRadar Comprehensive Source Testing")
print("=" * 80)

results = defaultdict(lambda: defaultdict(list))

# Test RSS sources
print("\n[TESTING RSS SOURCES]")
print("=" * 80)

for name, url, category in RSS_SOURCES:
    print(f"\n{name} ({category})")
    print(f"  URL: {url}")

    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()

        feed = feedparser.parse(response.content)
        entry_count = len(feed.entries)

        if entry_count > 0:
            print(f"  Status: OK ({entry_count} entries)")
            results[category]['success'].append(name)
        else:
            print(f"  Status: WARNING (0 entries)")
            results[category]['warning'].append(name)

    except Exception as e:
        print(f"  Status: FAILED - {str(e)[:60]}")
        results[category]['failed'].append(name)

# Test HTML sources
print("\n\n[TESTING HTML SOURCES]")
print("=" * 80)

for name, url, category in HTML_SOURCES:
    print(f"\n{name} ({category})")
    print(f"  URL: {url}")

    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        # Basic check - if we can parse it, it's accessible
        print(f"  Status: OK (HTML accessible, {len(response.text)} bytes)")
        results[category]['success'].append(name)

    except Exception as e:
        print(f"  Status: FAILED - {str(e)[:60]}")
        results[category]['failed'].append(name)

# Test alternative sources
print("\n\n[TESTING ALTERNATIVE SOURCES]")
print("=" * 80)

for name, url in ALTERNATIVE_RSS_SOURCES:
    print(f"\n{name}")
    print(f"  URL: {url}")

    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()

        feed = feedparser.parse(response.content)
        entry_count = len(feed.entries)

        if entry_count > 0:
            print(f"  Status: SUCCESS ({entry_count} entries) - GOOD ALTERNATIVE!")
            results['ALTERNATIVES']['success'].append(name)
        else:
            print(f"  Status: WARNING (0 entries)")
            results['ALTERNATIVES']['warning'].append(name)

    except Exception as e:
        print(f"  Status: FAILED - {str(e)[:60]}")
        results['ALTERNATIVES']['failed'].append(name)

# Summary
print("\n\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

for category in ['NEW', 'EXISTING', 'VERIFY', 'ALTERNATIVES']:
    if category in results:
        print(f"\n{category} Sources:")
        for status in ['success', 'warning', 'failed']:
            if results[category][status]:
                print(f"  {status.upper()}: {len(results[category][status])}")
                for source in results[category][status]:
                    print(f"    - {source}")

# Calculate totals
total_tested = len(RSS_SOURCES) + len(HTML_SOURCES) + len(ALTERNATIVE_RSS_SOURCES)
total_success = sum(len(results[cat]['success']) for cat in results)
success_rate = (total_success / total_tested * 100) if total_tested > 0 else 0

print(f"\n{'=' * 80}")
print(f"Total tested: {total_tested}")
print(f"Total working: {total_success}")
print(f"Success rate: {success_rate:.1f}%")
print("=" * 80)

# Recommendations
print("\n[RECOMMENDATIONS]")
print("=" * 80)
if results['ALTERNATIVES']['success']:
    print("\nWorking alternatives found - consider adding:")
    for source in results['ALTERNATIVES']['success']:
        print(f"  + {source}")

if results['NEW']['failed']:
    print("\nNew sources that failed - consider disabling:")
    for source in results['NEW']['failed']:
        print(f"  - {source}")

print("\n")
