# Part 2 Methodology and Findings

The pipeline validates the nine-column schema before processing. Blank holiday values are converted to `None`; dates and categories are standardised; invalid dates and exact duplicates are removed; 0 K temperatures are replaced with valid month-specific medians; and rainfall above 9,000 mm is treated as an impossible sensor value and replaced with the median. Repeated timestamps with different weather descriptions are retained because they are not exact duplicates.

Features include hour, day of week, weekend and holiday flags, sine/cosine encodings, Celsius temperature, weather indicators, z-score scaling, quartile-based congestion and the documented high-risk proxy. Saved charts examine hourly demand, weekday/weekend differences, weather and temperature. The CLI provides summary, timestamp lookup, high-traffic and weekday/weekend comparison commands. Logs provide an auditable trail and distinguish milestones, recoverable changes and failures.
