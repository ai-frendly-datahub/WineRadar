# -*- coding: utf-8 -*-
"""Update sources.yaml to disable non-working sources."""

import yaml

# Sources that failed testing (404/403/DNS errors)
DISABLE_SOURCES = {
    'media_jancisrobinson_uk': 'RSS 404 error - Feed URL not found',
    'media_winesearcher_global': 'RSS 403 Forbidden - Bot protection',
    'media_vinetur_es': 'RSS 404 error - Feed URL not found',
    'media_worlds50best_uk': 'RSS 404 error - Feed URL not found',
    'media_austinwine_us': 'DNS resolution failed - Domain unavailable',
    'media_meininger_de': 'RSS 403 Forbidden - Subscription required',
}

# Read sources.yaml
with open('config/sources.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

# Update sources
updated_count = 0
for source in data['sources']:
    source_id = source.get('id')
    if source_id in DISABLE_SOURCES:
        if source.get('enabled', False):
            source['enabled'] = False
            reason = DISABLE_SOURCES[source_id]
            current_notes = source.get('notes', '')
            source['notes'] = f"{current_notes} [DISABLED: {reason}]"
            updated_count += 1
            print(f"Disabled: {source['name']} ({source_id})")
            print(f"  Reason: {reason}")

# Write back
with open('config/sources.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print(f"\nUpdated {updated_count} sources")
print("Sources.yaml has been updated successfully")
