# -*- coding: utf-8 -*-
"""데이터 소스 자동 모니터링 및 알림."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import feedparser
import yaml
from bs4 import BeautifulSoup

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class SourceMonitor:
    """데이터 소스의 상태를 모니터링하고 문제를 감지한다."""

    def __init__(self, sources_config_path: str | Path):
        """소스 모니터 초기화."""
        self.config_path = Path(sources_config_path)
        self.sources = self._load_sources()
        self.results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_sources": 0,
            "enabled_sources": 0,
            "tested_sources": 0,
            "passed": [],
            "failed": [],
            "warnings": [],
        }

    def _load_sources(self) -> list[dict[str, Any]]:
        """sources.yaml를 로드한다."""
        with open(self.config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("sources", [])

    def check_all_sources(self, enabled_only: bool = True) -> dict[str, Any]:
        """모든 소스를 검사한다."""
        sources_to_check = [
            s for s in self.sources
            if not enabled_only or s.get("enabled", False)
        ]

        self.results["total_sources"] = len(self.sources)
        self.results["enabled_sources"] = len([s for s in self.sources if s.get("enabled", False)])
        self.results["tested_sources"] = len(sources_to_check)

        for source in sources_to_check:
            source_id = source.get("id", "unknown")
            source_name = source.get("name", "Unknown")
            collection_method = source.get("config", {}).get("collection_method")

            print(f"Testing {source_name} ({source_id})...", end=" ")

            try:
                if collection_method == "rss":
                    self._check_rss_source(source)
                elif collection_method == "html":
                    self._check_html_source(source)
                else:
                    self.results["warnings"].append({
                        "id": source_id,
                        "name": source_name,
                        "issue": f"Unknown collection method: {collection_method}",
                    })
                    print("SKIP")
            except Exception as e:
                self.results["failed"].append({
                    "id": source_id,
                    "name": source_name,
                    "error": str(e)[:200],
                    "method": collection_method,
                })
                print(f"FAIL - {str(e)[:50]}")

        return self.results

    def _check_rss_source(self, source: dict[str, Any]) -> None:
        """RSS 소스를 검사한다."""
        source_id = source.get("id")
        source_name = source.get("name")
        list_url = source.get("config", {}).get("list_url")

        if not list_url:
            raise ValueError("No list_url configured")

        # Fetch RSS feed
        response = requests.get(
            list_url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        response.raise_for_status()

        # Parse feed
        feed = feedparser.parse(response.content)
        entry_count = len(feed.entries)

        if entry_count == 0:
            self.results["warnings"].append({
                "id": source_id,
                "name": source_name,
                "issue": "RSS feed has 0 entries",
                "url": list_url,
            })
            print(f"WARN - 0 entries")
        else:
            self.results["passed"].append({
                "id": source_id,
                "name": source_name,
                "method": "rss",
                "entries": entry_count,
                "url": list_url,
            })
            print(f"OK - {entry_count} entries")

    def _check_html_source(self, source: dict[str, Any]) -> None:
        """HTML 소스를 검사한다."""
        source_id = source.get("id")
        source_name = source.get("name")
        list_url = source.get("config", {}).get("list_url")
        article_selector = source.get("config", {}).get("article_selector")

        if not list_url:
            raise ValueError("No list_url configured")

        # Fetch HTML page
        response = requests.get(
            list_url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Try to find articles
        if article_selector:
            articles = soup.select(article_selector)
            article_count = len(articles)
        else:
            # Fallback to generic 'a' tags
            articles = soup.find_all("a", href=True)
            article_count = len(articles)

        if article_count == 0:
            self.results["warnings"].append({
                "id": source_id,
                "name": source_name,
                "issue": f"No articles found with selector: {article_selector or 'a'}",
                "url": list_url,
            })
            print(f"WARN - 0 articles")
        else:
            self.results["passed"].append({
                "id": source_id,
                "name": source_name,
                "method": "html",
                "articles": article_count,
                "url": list_url,
            })
            print(f"OK - {article_count} links")

    def generate_report(self, output_path: str | Path | None = None) -> str:
        """모니터링 결과 리포트를 생성한다."""
        output_path = Path(output_path or "docs/SOURCE_MONITORING.md")

        passed_count = len(self.results["passed"])
        failed_count = len(self.results["failed"])
        warning_count = len(self.results["warnings"])
        tested = self.results["tested_sources"]

        success_rate = (passed_count / tested * 100) if tested > 0 else 0.0

        content = f"""# WineRadar Source Monitoring Report

**Generated**: {self.results["timestamp"]}

---

## Summary

| Metric | Value |
|--------|-------|
| Total Sources | {self.results["total_sources"]} |
| Enabled Sources | {self.results["enabled_sources"]} |
| Tested Sources | {self.results["tested_sources"]} |
| **Passed** | **{passed_count}** ✅ |
| **Failed** | **{failed_count}** ❌ |
| **Warnings** | **{warning_count}** ⚠️ |
| **Success Rate** | **{success_rate:.1f}%** |

---

## ✅ Passed Sources ({passed_count})

"""

        for source in self.results["passed"]:
            content += f"""### {source['name']}
- **ID**: `{source['id']}`
- **Method**: {source['method']}
- **Items**: {source.get('entries', source.get('articles', 'N/A'))}
- **URL**: {source['url']}

"""

        content += f"""---

## ❌ Failed Sources ({failed_count})

"""

        if failed_count == 0:
            content += "No failed sources! 🎉\n\n"
        else:
            for source in self.results["failed"]:
                content += f"""### {source['name']}
- **ID**: `{source['id']}`
- **Method**: {source['method']}
- **Error**: `{source['error']}`
- **Action Required**: Investigate and update configuration

"""

        content += f"""---

## ⚠️ Warnings ({warning_count})

"""

        if warning_count == 0:
            content += "No warnings!\n\n"
        else:
            for source in self.results["warnings"]:
                content += f"""### {source['name']}
- **ID**: `{source['id']}`
- **Issue**: {source['issue']}
- **URL**: {source.get('url', 'N/A')}

"""

        content += """---

## Recommendations

"""

        if failed_count > 0:
            content += f"""### Critical ({failed_count} sources)
1. Review failed sources above
2. Update URLs or selectors in `config/sources.yaml`
3. Consider disabling sources that are permanently unavailable
4. Re-run monitoring after fixes: `python tools/monitor_sources.py`

"""

        if warning_count > 0:
            content += f"""### Attention ({warning_count} sources)
1. Sources with 0 entries may have temporary issues
2. Check HTML selectors for HTML sources
3. Monitor for 2-3 days before taking action

"""

        if success_rate >= 90:
            content += """### Overall Status: Excellent ✅
Source health is good. Continue regular monitoring.

"""
        elif success_rate >= 75:
            content += """### Overall Status: Good ⚠️
Some sources need attention. Review warnings and failed sources.

"""
        else:
            content += """### Overall Status: Needs Attention ❌
Multiple sources are failing. Immediate action required.

"""

        content += f"""---

## Next Steps

1. **Weekly monitoring**: Run this script every week
2. **Update documentation**: Keep SOURCE_STATUS.md in sync
3. **GitHub Actions integration**: Consider adding to CI workflow
4. **Alerting**: Set up notifications for critical failures

**Last updated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
"""

        output_path.write_text(content, encoding="utf-8")
        return str(output_path)


def main():
    """메인 함수."""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor WineRadar data sources")
    parser.add_argument(
        "--config",
        default="config/sources.yaml",
        help="Path to sources.yaml (default: config/sources.yaml)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Test all sources, including disabled ones"
    )
    parser.add_argument(
        "--output",
        default="docs/SOURCE_MONITORING.md",
        help="Output report path (default: docs/SOURCE_MONITORING.md)"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("WineRadar Source Monitoring")
    print("=" * 80)
    print()

    monitor = SourceMonitor(args.config)
    results = monitor.check_all_sources(enabled_only=not args.all)

    print()
    print("=" * 80)
    print("Monitoring Complete")
    print("=" * 80)
    print(f"Tested: {results['tested_sources']} sources")
    print(f"Passed: {len(results['passed'])} [OK]")
    print(f"Failed: {len(results['failed'])} [FAIL]")
    print(f"Warnings: {len(results['warnings'])} [WARN]")
    print()

    report_path = monitor.generate_report(args.output)
    print(f"Report saved to: {report_path}")
    print()

    # Exit with error code if there are failures
    if len(results['failed']) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
