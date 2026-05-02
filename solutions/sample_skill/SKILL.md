---
name: anomaly-triage
description: Triages anomalous energy-consumption sites by enriching with business-unit and region context, comparing to a 30-day baseline, and proposing 2-3 plausible causes. Use when the user asks to investigate energy anomalies, unusual usage spikes, or flagged sites in the genie_code_lab dataset.
---

# Anomaly triage workflow

When the user asks to investigate one or more anomalous sites, follow these
steps in order. Do **not** skip steps even if the user's question is broad.

## 1. Pull the candidate set
Query `workspace.genie_code_lab.daily_site_consumption` for rows where
`anomaly_flag = true`, filtered to the requested time window. If no window
is given, default to the last 7 days.

## 2. Enrich with site, business unit, and region context
The gold table already carries `business_unit_name` and `region_name`. Join
to `workspace.genie_code_lab.sites` to add `site_name`, `city`, `state`, and
`square_footage` for each anomalous (site, day).

## 3. Quantify the deviation
Use the `deviation_pct` column already produced by the pipeline. If for some
reason it is missing, recompute it from `total_kwh`, `site_mean_kwh`, and
`site_stddev_kwh`.

## 4. Cross-reference recent meter health
For each anomalous (site, day), query `workspace.genie_code_lab.meter_readings`
to count `status = 'warning'` and `status = 'error'` rows in the same day.
A spike in warnings strongly suggests a meter or equipment issue rather
than a true consumption change.

## 5. Produce a markdown report

Format the report exactly as below. Be concise — no preamble, no
"here is your report" lead-in.

```markdown
## Anomaly triage — <window>

**Anomalies found:** <N> across <M> sites.
**By business unit:** <BU name>: <count>; <BU name>: <count>; ...

### Top 3 by deviation

1. **<site_name>** (<city>, <state>) — <site_type>, <business_unit_name>, <region_name>
   - +<deviation_pct>% above 30-day mean (<total_kwh> kWh vs. baseline ~<site_mean_kwh> kWh)
   - <warning_count> warnings, <error_count> errors that day
   - **Likely causes:**
     - <cause 1, drawing on site_type, square_footage, weather/temperature_c>
     - <cause 2, drawing on meter health and recent error rate>

(repeat for #2 and #3)

### Next steps
- Sites that warrant human follow-up: <list>
- Sites that look like meter/equipment issues (high warnings): <list>
- Sites that look like genuine consumption anomalies (low warnings): <list>
```

## Notes
- If fewer than 3 anomalous sites exist in the window, list however many you
  found — don't pad with non-anomalous rows.
- Don't speculate about causes you can't ground in the data. "Possibly a
  heatwave" is fine if `temperature_c` was elevated; "possibly a server
  upgrade" is not, because we have no data to support it.
- Site types vary widely in absolute consumption: a factory legitimately
  draws far more than an office. Always lead with `deviation_pct`, never
  with raw `total_kwh`.
