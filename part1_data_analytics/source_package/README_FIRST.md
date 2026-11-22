# Part 1 Traffic Analytics

This standalone package addresses the task list supplied on 26 October 2026. Start with report/Part_1_Worked_Answers.docx for all answers and report/Data_Analytics_Insights_Report.docx for the required two-page summary.

## Deliverables

1. sql/traffic.sqlite contains the imported source and hourly data. sql/queries.sql has twelve SELECT statements covering annual/holiday results, verification, statistics, correlation, probabilities, weather and chart summaries. All result tables are saved as CSV under results/.
2. report/Part_1_Worked_Answers.docx contains calculations, interpretations, quality findings and charts for Tasks 1.1–4.3. statistics.json and probability_analysis.csv contain machine-readable results.
3. PowerBI/Traffic_Intelligence.pbip is the prepared native report project. It now uses report content version 2.0.0 (connection version 4.0 remains separate), standard hexadecimal identifiers, two pages, four required charts, three KPI cards, three slicers, summary tables, an embedded original CSV and complete Power Query cleaning. Twenty report/property JSON definitions pass Microsoft schema checks. Desktop loading, native rendering, PBIX export and screenshots remain unverified because Desktop access is unavailable here. The earlier version failed to show pages on the user's laptop; this package corrects a likely compatibility issue but does not claim a verified fix.
4. report/Data_Analytics_Insights_Report.docx is the required two-page insights report.

## Open the dashboard

Extract the ZIP first. In PowerBI double-click Traffic_Intelligence.pbip. Keep the two supporting folders beside it. Expected page tabs: Traffic Intelligence; Annual and Data Quality. Refresh, inspect the visuals/slicers, then Save As a Power BI report (.pbix). Do not rename PBIP or ZIP to PBIX.

If the prepared project still fails to render, follow report/Power_BI_Step_Guide.docx. Start File > New, confirm Page 1, import data/Traffic_PowerBI_Ready.csv. It already includes Hour, Date, Year, Temperature Celsius and Traffic Category. For raw-data Power Query assessment evidence, create TrafficRaw and TrafficHourly using the supplied M queries, as explained in the guide. The prepared CSV alone is a display fallback, not proof of completing raw Power Query transformations.

Traffic_Dashboard.html is a self-contained interactive browser companion; it is not represented as a Power BI file. Static task charts are in charts/.

## Data contract

Source: 48,204 records and nine columns. Literal holiday None is valid text, not a blank. Remove 17 identical records. Ten zero-K source readings and one rain value above 9,000 mm are repaired with training-period monthly medians (through 2016), consistent with the broader capstone. Repeated weather records collapse to one observed hour, prioritising Thunderstorm/Squall, Snow/Fog, Mist/Haze/Smoke, Rain, Drizzle and Clouds/Clear with alphabetical tie-breaking. Traffic is the per-hour median, never a sum across weather duplicates. Holidays are expanded only to observed hours on the marked date. Missing calendar periods are not invented. The output has 40,575 unique hours.

Main analysis uses hourly data; raw-record results are explicitly a comparison. Clouds is highest in raw records, Smoke in primary-hourly records. Smoke has only two hours and Squall four: these are unstable categories. New Year 2015 is unavailable; 2018 is an explicitly additional comparison. SD and variance are sample estimates (n−1). Congestion is >5,500. Traffic bands are Low <4,500, Medium 4,500–5,500 and High >5,500.

## Reproduce numerical outputs

Python 3.12 with pandas and numpy:

```bash
python tools/run_part1.py
python tools/make_charts.py
```

Other optional tools:
- build_documents.py requires python-docx and pandas.
- build_project.py rebuilds the native project using the supplied M/DAX resources.
- validate_powerbi.py requires requests/jsonschema and internet access to Microsoft's schemas.

The SQLite database and CSVs are already built. SQLite needs SQRT support for the statistics/correlation SELECTs; the bundled Python SQLite used here supports it. Results of all twelve queries were executed and cross-checked with Python.
