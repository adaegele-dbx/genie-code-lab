# Sample Genie Space Tuning for Part 3b

Use these as a fallback if your Genie space struggles to answer the three
benchmark questions in Part 3b. Paste the description into the space's
**Description** field and the per-table instructions into the corresponding
table's **Instructions** field via the Genie space editor.

---

## Genie space description

```
Energy operations Q&A space for our internal site portfolio. Backed by daily
per-site consumption summaries from
`workspace.genie_code_lab.daily_site_consumption`, joined with site metadata
in `workspace.genie_code_lab.sites`, and dimension tables for `regions` and
`business_units`.

Use this space to investigate anomalous energy usage, compare consumption
across site types or business units, and rank sites by total kWh, peak demand,
or deviation from baseline. The `anomaly_flag` column is computed at pipeline
time as "this day's total_kwh exceeds 2 standard deviations above the site's
30-day mean" — treat any question about "spikes," "unusual usage," or
"outliers" as filtering on this flag.
```

## Per-table tuning notes

### `daily_site_consumption`
- Already carries `business_unit_name` and `region_name` — no need to join the
  dimension tables for most BU- or region-level questions
- `total_kwh` is the daily sum of kwh_consumed for the site
- `peak_kw` is the highest 15-minute kw_demand observed that day
- `anomaly_flag` is the canonical answer to questions about "anomalies,"
  "unusual usage," "spikes," or "outliers"
- `deviation_pct` is the % deviation from the site's 30-day mean — use
  this when ranking severity

### `sites`
- `site_type` values: factory, warehouse, office, data_center, retail
- Factories and data centers consume far more in absolute terms; for fair
  comparisons, normalize by `square_footage` (kWh per sq ft)

### `regions` / `business_units`
- Pure dimension lookups. `regions.timezone` is useful only when displaying
  reading_timestamps in local time.

## Suggested SQL for common questions

### "Which business unit had the most anomalies last week?"
```sql
SELECT business_unit_name, COUNT(*) AS anomaly_count
FROM   workspace.genie_code_lab.daily_site_consumption
WHERE  anomaly_flag = TRUE
  AND  reading_date >= current_date - INTERVAL 7 DAYS
GROUP BY business_unit_name
ORDER BY anomaly_count DESC
```

### "Top 5 sites by total kWh in the past 14 days"
```sql
SELECT s.site_name, d.site_type, d.business_unit_name, SUM(d.total_kwh) AS total_kwh_14d
FROM   workspace.genie_code_lab.daily_site_consumption d
JOIN   workspace.genie_code_lab.sites s USING (site_id)
WHERE  d.reading_date >= current_date - INTERVAL 14 DAYS
GROUP BY s.site_name, d.site_type, d.business_unit_name
ORDER BY total_kwh_14d DESC
LIMIT 5
```
