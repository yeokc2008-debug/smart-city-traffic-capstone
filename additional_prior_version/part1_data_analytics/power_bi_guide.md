# Power BI Dashboard Build Guide

Load the CSV in Power BI Desktop. In Power Query, set `date_time` to Date/Time, numeric fields to decimal/whole number, and replace null `holiday` with `None`. Add `Hour = Time.Hour([date_time])`, `Temperature C = [temp] - 273.15`, and a conditional `Traffic Category`: Low below 4500, Medium from 4500 through 5500, High above 5500. Do not remove repeated timestamps unless all nine fields are exact duplicates.

Create: (1) line chart of daily mean traffic filtered to 2015–2017; (2) column chart of mean traffic by hour filtered to 2017; (3) bar chart of mean traffic by `weather_main`; (4) scatter plot with temperature and traffic; (5) cards for count of rows, mean traffic and mean temperature; and slicers for hour, weather and category. Use the CSV files in `outputs/` to validate totals.
