# WineRadar Source Monitoring Report

**Generated**: 2025-11-19T09:10:18.556536+00:00

---

## Summary

| Metric | Value |
|--------|-------|
| Total Sources | 40 |
| Enabled Sources | 18 |
| Tested Sources | 18 |
| **Passed** | **16** ✅ |
| **Failed** | **2** ❌ |
| **Warnings** | **0** ⚠️ |
| **Success Rate** | **88.9%** |

---

## ✅ Passed Sources (16)

### Wine21
- **ID**: `media_wine21_kr`
- **Method**: html
- **Items**: 10
- **URL**: https://www.wine21.com/11_news/news_list.html

### WINE WHAT!?
- **ID**: `media_winewhat_jp`
- **Method**: rss
- **Items**: 10
- **URL**: https://wine-what.jp/feed/

### Decanter
- **ID**: `media_decanter_global`
- **Method**: rss
- **Items**: 30
- **URL**: https://www.decanter.com/feed/

### The Drinks Business
- **ID**: `media_drinksbusiness_uk`
- **Method**: rss
- **Items**: 30
- **URL**: https://www.thedrinksbusiness.com/feed/

### Terre de Vins
- **ID**: `media_terredevins_fr`
- **Method**: rss
- **Items**: 10
- **URL**: https://www.terredevins.com/feed

### Gambero Rosso
- **ID**: `media_gambero_it`
- **Method**: rss
- **Items**: 500
- **URL**: https://www.gamberorosso.it/feed/

### Wine Enthusiast
- **ID**: `media_wineenthusiast_us`
- **Method**: rss
- **Items**: 10
- **URL**: https://www.wineenthusiast.com/feed/

### Vinography
- **ID**: `media_vinography_us`
- **Method**: rss
- **Items**: 20
- **URL**: https://www.vinography.com/feed

### Enolife
- **ID**: `media_enolife_ar`
- **Method**: rss
- **Items**: 10
- **URL**: https://enolife.com.ar/feed/

### Wine & Spirits Magazine
- **ID**: `media_winemag_us`
- **Method**: rss
- **Items**: 10
- **URL**: https://www.winemag.com/feed/

### Vinogusto
- **ID**: `media_vinogusto_it`
- **Method**: rss
- **Items**: 10
- **URL**: https://www.vinogusto.com/feed/

### Wine Magazine South Africa
- **ID**: `media_winemag_za`
- **Method**: rss
- **Items**: 10
- **URL**: https://www.winemag.co.za/feed/

### ACE Vinos
- **ID**: `media_acevinos_es`
- **Method**: rss
- **Items**: 10
- **URL**: https://www.acenologia.com/feed/

### VinePair
- **ID**: `media_vinepair_us`
- **Method**: rss
- **Items**: 55
- **URL**: https://vinepair.com/wine-blog/feed/

### Punch
- **ID**: `media_punch_us`
- **Method**: rss
- **Items**: 10
- **URL**: https://punchdrink.com/feed/

### Tim Atkin MW
- **ID**: `media_timatkin_uk`
- **Method**: rss
- **Items**: 10
- **URL**: https://www.timatkin.com/feed/

---

## ❌ Failed Sources (2)

### Wine Review
- **ID**: `media_winereview_kr`
- **Method**: html
- **Error**: `404 Client Error: Not Found for url: https://winereview.co.kr/news`
- **Action Required**: Investigate and update configuration

### La Revue du vin de France
- **ID**: `media_larvf_fr`
- **Method**: html
- **Error**: `404 Client Error: Not Found for url: https://www.larvf.com/actualites`
- **Action Required**: Investigate and update configuration

---

## ⚠️ Warnings (0)

No warnings!

---

## Recommendations

### Critical (2 sources)
1. Review failed sources above
2. Update URLs or selectors in `config/sources.yaml`
3. Consider disabling sources that are permanently unavailable
4. Re-run monitoring after fixes: `python tools/monitor_sources.py`

### Overall Status: Good ⚠️
Some sources need attention. Review warnings and failed sources.

---

## Next Steps

1. **Weekly monitoring**: Run this script every week
2. **Update documentation**: Keep SOURCE_STATUS.md in sync
3. **GitHub Actions integration**: Consider adding to CI workflow
4. **Alerting**: Set up notifications for critical failures

**Last updated**: 2025-11-19 09:10 UTC
