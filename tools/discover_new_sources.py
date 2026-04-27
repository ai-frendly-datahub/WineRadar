"""신규 데이터 소스 발굴 및 검증."""

from __future__ import annotations

from typing import Any

import feedparser
import requests


# 발굴 대상 소스 목록
CANDIDATE_SOURCES = [
    # === 아시아 시장 강화 (현재 16.7% → 목표 25%) ===
    {
        "name": "Wine Review Korea",
        "url": "https://www.winereview.co.kr/feed/",
        "method": "rss",
        "region": "ASIA",
        "country": "KR",
        "tier": "T3_professional",
        "note": "Alternative RSS for Wine Review",
    },
    {
        "name": "Asian Wine Review",
        "url": "https://www.asianwinereview.com/feed/",
        "method": "rss",
        "region": "ASIA",
        "country": "HK",
        "tier": "T3_professional",
        "note": "Asian wine market coverage",
    },
    {
        "name": "Vino Joy News",
        "url": "https://www.vinojoynews.com/feed/",
        "method": "rss",
        "region": "ASIA",
        "country": "CN",
        "tier": "T3_professional",
        "note": "China wine market",
    },
    {
        "name": "Napa Valley Vintners",
        "url": "https://napavintners.com/press_releases/feed/",
        "method": "rss",
        "region": "NEW_WORLD",
        "country": "US",
        "tier": "T2_expert",
        "note": "Napa Valley official news",
    },
    # === 유럽 소스 추가 (구대륙 균형) ===
    {
        "name": "The Wine Merchant",
        "url": "https://www.thewinemerchant.com/blog/feed/",
        "method": "rss",
        "region": "OLD_WORLD",
        "country": "GB",
        "tier": "T3_professional",
        "note": "UK wine merchant insights",
    },
    {
        "name": "Dr Vino",
        "url": "https://www.drvino.com/feed/",
        "method": "rss",
        "region": "OLD_WORLD",
        "country": "IT",
        "tier": "T3_professional",
        "note": "Italian wine culture",
    },
    {
        "name": "Vins & Millesimes",
        "url": "https://www.vins-millesimes.com/feed/",
        "method": "rss",
        "region": "OLD_WORLD",
        "country": "FR",
        "tier": "T3_professional",
        "note": "French wine news",
    },
    # === 신대륙 추가 (호주/뉴질랜드/남미) ===
    {
        "name": "Wine Australia",
        "url": "https://www.wineaustralia.com/news/feed",
        "method": "rss",
        "region": "NEW_WORLD",
        "country": "AU",
        "tier": "T1_authoritative",
        "note": "Australian wine authority",
    },
    {
        "name": "The Real Review",
        "url": "https://www.therealreview.com/feed/",
        "method": "rss",
        "region": "NEW_WORLD",
        "country": "AU",
        "tier": "T3_professional",
        "note": "Australian wine reviews",
    },
    {
        "name": "Catena Institute",
        "url": "https://www.catenainstitute.com/feed/",
        "method": "rss",
        "region": "NEW_WORLD",
        "country": "AR",
        "tier": "T2_expert",
        "note": "Argentine wine research",
    },
    # === 전문가 소스 (T2 tier 강화) ===
    {
        "name": "Jamie Goode's Wine Blog",
        "url": "https://www.wineanorak.com/feed",
        "method": "rss",
        "region": "OLD_WORLD",
        "country": "GB",
        "tier": "T2_expert",
        "note": "Wine scientist and critic",
    },
    {
        "name": "Eric Asimov",
        "url": "https://www.nytimes.com/column/eric-asimov-wine-school?rss=1",
        "method": "rss",
        "region": "NEW_WORLD",
        "country": "US",
        "tier": "T2_expert",
        "note": "NY Times wine critic",
    },
    {
        "name": "Jeb Dunnuck",
        "url": "https://www.jebdunnuck.com/feed/",
        "method": "rss",
        "region": "NEW_WORLD",
        "country": "US",
        "tier": "T2_expert",
        "note": "Independent wine critic",
    },
    # === Gambero Rosso 비중 감소용 (이탈리아 대안) ===
    {
        "name": "Intravino",
        "url": "https://www.intravino.com/feed/",
        "method": "rss",
        "region": "OLD_WORLD",
        "country": "IT",
        "tier": "T3_professional",
        "note": "Italian wine magazine - Gambero alternative",
    },
    {
        "name": "Wine News",
        "url": "https://www.winenews.it/feed/",
        "method": "rss",
        "region": "OLD_WORLD",
        "country": "IT",
        "tier": "T3_professional",
        "note": "Italian wine industry news",
    },
]


def test_source(source: dict[str, Any]) -> dict[str, Any]:
    """소스를 테스트하고 결과를 반환한다."""
    result = {
        "name": source["name"],
        "url": source["url"],
        "method": source["method"],
        "status": "unknown",
        "entries": 0,
        "error": None,
    }

    try:
        if source["method"] == "rss":
            response = requests.get(
                source["url"],
                timeout=10,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            response.raise_for_status()

            feed = feedparser.parse(response.content)
            entry_count = len(feed.entries)

            if entry_count > 0:
                result["status"] = "success"
                result["entries"] = entry_count
            else:
                result["status"] = "warning"
                result["error"] = "0 entries in feed"

        else:
            # HTML method - basic check
            response = requests.get(
                source["url"],
                timeout=10,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            response.raise_for_status()
            result["status"] = "success"
            result["entries"] = len(response.text)

    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)[:100]

    return result


def main():
    """모든 후보 소스를 테스트한다."""
    print("=" * 80)
    print("WineRadar New Source Discovery")
    print("=" * 80)
    print(f"Testing {len(CANDIDATE_SOURCES)} candidate sources...")
    print()

    success_sources = []
    failed_sources = []
    warning_sources = []

    for source in CANDIDATE_SOURCES:
        print(f"Testing {source['name']}...", end=" ")
        result = test_source(source)

        if result["status"] == "success":
            print(f"OK - {result['entries']} entries")
            success_sources.append({**source, **result})
        elif result["status"] == "warning":
            print(f"WARN - {result['error']}")
            warning_sources.append({**source, **result})
        else:
            print(f"FAIL - {result['error'][:50]}")
            failed_sources.append({**source, **result})

    print()
    print("=" * 80)
    print("Discovery Results")
    print("=" * 80)
    print(f"Tested: {len(CANDIDATE_SOURCES)} sources")
    print(f"Success: {len(success_sources)} [OK]")
    print(f"Warnings: {len(warning_sources)} [WARN]")
    print(f"Failed: {len(failed_sources)} [FAIL]")
    print()

    # 지역별 분석
    region_count = {}
    tier_count = {}

    for source in success_sources:
        region = source.get("region", "Unknown")
        tier = source.get("tier", "Unknown")

        region_count[region] = region_count.get(region, 0) + 1
        tier_count[tier] = tier_count.get(tier, 0) + 1

    print("Regional Distribution (Successful Sources):")
    for region, count in sorted(region_count.items()):
        print(f"  {region}: {count}")
    print()

    print("Trust Tier Distribution:")
    for tier, count in sorted(tier_count.items()):
        print(f"  {tier}: {count}")
    print()

    # 권장 추가 소스
    print("=" * 80)
    print("Recommended Sources to Add")
    print("=" * 80)

    # 우선순위 계산 (아시아 > T2 expert > Gambero 대안)
    prioritized = []
    for source in success_sources:
        priority_score = 0

        # 아시아 소스 우선 (Gambero 균형 맞추기)
        if source.get("region") == "ASIA":
            priority_score += 10

        # T2 expert 우선 (품질 향상)
        if source.get("tier") == "T2_expert":
            priority_score += 5

        # T1 authoritative (공신력)
        if source.get("tier") == "T1_authoritative":
            priority_score += 7

        # 이탈리아 대안 (Gambero 비중 감소)
        if source.get("country") == "IT" and "Gambero" in source.get("note", ""):
            priority_score += 3

        prioritized.append({**source, "priority": priority_score})

    prioritized.sort(key=lambda x: x["priority"], reverse=True)

    for i, source in enumerate(prioritized[:10], 1):
        print(f"{i}. {source['name']}")
        print(f"   Region: {source['region']}, Tier: {source['tier']}")
        print(f"   Entries: {source['entries']}, Priority: {source['priority']}")
        print(f"   Note: {source['note']}")
        print()

    print("Copy these sources to config/sources.yaml to add them to WineRadar.")


if __name__ == "__main__":
    main()
