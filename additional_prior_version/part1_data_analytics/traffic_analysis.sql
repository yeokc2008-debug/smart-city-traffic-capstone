-- SQLite queries for Capstone Part 1
SELECT COUNT(*) AS rows_loaded FROM traffic;
SELECT strftime('%Y',date_time) AS year, SUM(traffic_volume) AS total_volume
FROM traffic WHERE strftime('%Y',date_time) BETWEEN '2012' AND '2017' GROUP BY year ORDER BY year;
WITH annual AS (SELECT CAST(strftime('%Y',date_time) AS INT) year, SUM(traffic_volume) total FROM traffic GROUP BY year)
SELECT year,total,total-LAG(total) OVER(ORDER BY year) AS annual_change FROM annual WHERE year BETWEEN 2012 AND 2017;
SELECT CAST(strftime('%Y',date_time) AS INT) year, holiday, AVG(temp) avg_temp_k, AVG(traffic_volume) avg_traffic
FROM traffic WHERE year IN (2015,2016,2017) AND holiday IN ("New Years Day","Labor Day") GROUP BY year,holiday;
