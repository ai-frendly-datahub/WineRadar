"""Quick EDA for WineRadar data."""

from pathlib import Path

import duckdb
import pandas as pd


db_path = Path("data/wineradar.duckdb")
conn = duckdb.connect(str(db_path), read_only=True)

print("=" * 70)
print("WineRadar Data Analysis Report")
print("=" * 70)

# Load data
df = conn.execute("SELECT * FROM urls").df()
df_entities = conn.execute("SELECT * FROM url_entities").df()

# Overall stats
print("\n[Overall Statistics]")
print(f"  - Total articles: {len(df):,}")
print(f"  - Active sources: {df['source_name'].nunique()}")
print(f"  - Date range: {df['published_at'].min().date()} ~ {df['published_at'].max().date()}")
print(f"  - Average score: {df['score'].mean():.2f}")

# By source
print("\n[Articles by Source]")
source_counts = df["source_name"].value_counts()
for source, count in source_counts.items():
    pct = (count / len(df)) * 100
    print(f"  - {source}: {count} ({pct:.1f}%)")

# Average scores
print("\n[Average Score by Source]")
source_scores = df.groupby("source_name")["score"].mean().sort_values(ascending=False)
for source, score in source_scores.items():
    print(f"  - {source}: {score:.2f}")

# By continent
print("\n[Articles by Continent]")
continent_counts = df["continent"].value_counts()
for continent, count in continent_counts.items():
    pct = (count / len(df)) * 100
    print(f"  - {continent}: {count} ({pct:.1f}%)")

# Top countries
print("\n[Top 10 Countries]")
country_counts = df["country"].value_counts().head(10)
for i, (country, count) in enumerate(country_counts.items(), 1):
    print(f"  {i}. {country}: {count}")

# Trust tiers
print("\n[Trust Tiers]")
trust_counts = df["trust_tier"].value_counts()
for tier, count in trust_counts.items():
    pct = (count / len(df)) * 100
    print(f"  - {tier}: {count} ({pct:.1f}%)")

# Entity stats
print("\n[Entity Statistics]")
print(f"  - Total entities: {len(df_entities):,}")
entity_type_counts = df_entities["entity_type"].value_counts()
for etype, count in entity_type_counts.items():
    print(f"  - {etype}: {count}")

# Top grapes
print("\n[Top 10 Grape Varieties]")
grape_entities = df_entities[df_entities["entity_type"] == "grape_variety"]
if len(grape_entities) > 0:
    grapes = grape_entities["entity_value"].value_counts().head(10)
    for i, (grape, count) in enumerate(grapes.items(), 1):
        print(f"  {i}. {grape}: {count} mentions")

# Top regions
print("\n[Top 10 Wine Regions]")
region_entities = df_entities[df_entities["entity_type"] == "region"]
if len(region_entities) > 0:
    regions = region_entities["entity_value"].value_counts().head(10)
    for i, (region, count) in enumerate(regions.items(), 1):
        print(f"  {i}. {region}: {count} mentions")

# Top wineries
print("\n[Top 10 Wineries]")
winery_entities = df_entities[df_entities["entity_type"] == "winery"]
if len(winery_entities) > 0:
    wineries = winery_entities["entity_value"].value_counts().head(10)
    for i, (winery, count) in enumerate(wineries.items(), 1):
        print(f"  {i}. {winery}: {count} mentions")

# Recent activity
df["date"] = pd.to_datetime(df["published_at"]).dt.date
daily_counts = df["date"].value_counts().sort_index()
print("\n[Last 7 Days Activity]")
for date, count in daily_counts.tail(7).items():
    print(f"  - {date}: {count} articles")

# Averages
days_active = (df["published_at"].max() - df["published_at"].min()).days + 1
print("\n[Average Statistics]")
print(f"  - Daily average: {len(df) / days_active:.1f} articles/day")
print(f"  - Entities per article: {len(df_entities) / len(df):.1f}")

# Score distribution
print("\n[Score Distribution]")
score_ranges = pd.cut(
    df["score"], bins=[0, 1, 2, 3, 4, 5], labels=["0-1", "1-2", "2-3", "3-4", "4-5"]
)
for range_label, count in score_ranges.value_counts().sort_index().items():
    pct = (count / len(df)) * 100
    print(f"  - {range_label}: {count} ({pct:.1f}%)")

# Content type
print("\n[Content Types]")
content_counts = df["content_type"].value_counts()
for ctype, count in content_counts.items():
    pct = (count / len(df)) * 100
    print(f"  - {ctype}: {count} ({pct:.1f}%)")

conn.close()

print("\n" + "=" * 70)
print("[Analysis Complete!]")
print("=" * 70)
