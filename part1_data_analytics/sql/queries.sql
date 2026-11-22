-- Raw-record sums are record-weighted and can double count hours.
SELECT strftime('%Y',date_time) year, COUNT(*) records, COUNT(DISTINCT date_time) observed_hours,
 SUM(traffic_volume) total_record_volume, AVG(traffic_volume) average_traffic
FROM traffic_raw WHERE strftime('%Y',date_time) BETWEEN '2012' AND '2017' GROUP BY 1;
-- Preferred annual totals from unique observed hours, missing hours are not zero.
WITH annual AS (SELECT strftime('%Y',date_time) year,COUNT(*) observed_hours,
 SUM(traffic_volume) total_observed_traffic,AVG(traffic_volume) average_traffic
 FROM traffic_hourly WHERE strftime('%Y',date_time) BETWEEN '2012' AND '2017' GROUP BY 1)
SELECT *,total_observed_traffic-LAG(total_observed_traffic) OVER(ORDER BY year) change,
 100.0*(total_observed_traffic-LAG(total_observed_traffic) OVER(ORDER BY year))/LAG(total_observed_traffic) OVER(ORDER BY year) change_pct FROM annual;
-- Original holiday-labelled records (typically midnight only).
SELECT strftime('%Y',date_time) year,holiday,AVG(temp) kelvin,AVG(temp)-273.15 celsius,COUNT(*) n
 FROM traffic_raw WHERE holiday IN ('New Years Day','Labor Day') AND strftime('%Y',date_time) BETWEEN '2015' AND '2017' GROUP BY 1,2;
-- Full observed holiday date after date-level holiday propagation.
SELECT strftime('%Y',date_time) year,holiday,AVG(temp) kelvin,AVG(temp)-273.15 celsius,COUNT(*) n
 FROM traffic_hourly WHERE holiday IN ('New Years Day','Labor Day') AND strftime('%Y',date_time) BETWEEN '2015' AND '2017' GROUP BY 1,2;
SELECT COUNT(*) rows,COUNT(DISTINCT date_time) hours,MIN(date_time),MAX(date_time) FROM traffic_raw;

-- Transparent substitute for unavailable New Year 2015
SELECT strftime('%Y',date_time) year,holiday,AVG(temp) kelvin,AVG(temp)-273.15 celsius,COUNT(*) n FROM traffic_hourly WHERE holiday='New Years Day' AND strftime('%Y',date_time) IN ('2014','2016','2017','2018') GROUP BY 1,2;
-- Task 2.1 sample statistics. Variance and SD use denominator n-1.
WITH ordered AS (SELECT traffic_volume,ROW_NUMBER() OVER(ORDER BY traffic_volume) rn,COUNT(*) OVER() n FROM traffic_hourly),
m AS (SELECT AVG(traffic_volume) mu,COUNT(*) n FROM traffic_hourly)
SELECT m.n observed_hours,m.mu mean_traffic,
 (SELECT AVG(traffic_volume) FROM ordered WHERE rn IN ((n+1)/2,(n+2)/2)) median_traffic,
 SUM((traffic_volume-m.mu)*(traffic_volume-m.mu))/(m.n-1) sample_variance,
 SQRT(SUM((traffic_volume-m.mu)*(traffic_volume-m.mu))/(m.n-1)) sample_standard_deviation,
 MAX(traffic_volume)-MIN(traffic_volume) traffic_range FROM traffic_hourly CROSS JOIN m;
-- Task 2.2 Pearson correlation.
WITH m AS (SELECT AVG(temp) mt,AVG(traffic_volume) mv FROM traffic_hourly)
SELECT SUM((temp-mt)*(traffic_volume-mv))/SQRT(SUM((temp-mt)*(temp-mt))*SUM((traffic_volume-mv)*(traffic_volume-mv))) pearson_r FROM traffic_hourly CROSS JOIN m;
-- Tasks 3.1 and 3.2 probability, independence comparison and odds ratio.
WITH c AS (SELECT COUNT(*) n,SUM(traffic_volume>5500) congested,SUM(weather_main='Clear') clear,
 SUM(traffic_volume>5500 AND weather_main='Clear') clear_congested,
 SUM(traffic_volume>5500 AND temp>292) hot_congested,
 SUM(traffic_volume<=5500 AND weather_main='Clear') clear_not,
 SUM(traffic_volume>5500 AND weather_main='Clouds') clouds_congested,
 SUM(traffic_volume<=5500 AND weather_main='Clouds') clouds_not FROM traffic_hourly)
SELECT congested*1.0/n p_congestion,clear*1.0/n p_clear,clear_congested*1.0/n p_joint,
 clear_congested*1.0/congested p_clear_given_congestion,hot_congested*1.0/congested p_hot_given_congestion,
 (congested*1.0/n)*(clear*1.0/n) independence_product,
 clear_congested*1.0*clouds_not/(clear_not*clouds_congested) odds_ratio FROM c;
-- Task 4C hourly weather means and category sample counts.
SELECT weather_main,COUNT(*) observed_hours,AVG(traffic_volume) average_traffic FROM traffic_hourly GROUP BY weather_main ORDER BY average_traffic DESC;
-- Task 4A daily observed-hour averages for 2015, 2016 and 2017.
SELECT DATE(date_time) date,strftime('%Y',date_time) year,COUNT(*) observed_hours,AVG(traffic_volume) average_traffic FROM traffic_hourly WHERE strftime('%Y',date_time) IN ('2015','2016','2017') GROUP BY 1,2;
-- Task 4B hourly traffic averages for 2017.
SELECT CAST(strftime('%H',date_time) AS INTEGER) hour,COUNT(*) observed_hours,AVG(traffic_volume) average_traffic FROM traffic_hourly WHERE strftime('%Y',date_time)='2017' GROUP BY 1 ORDER BY 1;
