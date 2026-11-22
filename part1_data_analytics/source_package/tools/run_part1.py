"""Rebuild the Part 1 database/results from included inputs, using read-only SELECTs."""
import logging,sqlite3,sys,json
from pathlib import Path
import pandas as pd
logger=logging.getLogger(__name__)
ROOT=Path(__file__).resolve().parents[1]
def run():
    raw=pd.read_csv(ROOT/'data/Metro_Interstate_Traffic_Volume.csv',keep_default_na=False)
    hourly=pd.read_csv(ROOT/'data/traffic_clean.csv',keep_default_na=False)
    if not hourly.date_time.is_unique:raise ValueError('Cleaned input must have unique timestamps')
    with sqlite3.connect(ROOT/'sql/traffic.sqlite') as con:
        raw.to_sql('traffic_raw',con,if_exists='replace',index=False);hourly.to_sql('traffic_hourly_materialized',con,if_exists='replace',index=False)
        con.execute('DROP VIEW IF EXISTS traffic_hourly');con.execute('CREATE VIEW traffic_hourly AS SELECT * FROM traffic_hourly_materialized')
        names=['annual_raw','annual_hourly','holiday_raw','holiday_daily','verification','holiday_substitute','traffic_statistics','temperature_correlation','probability_analysis','weather_summary','daily_2015_2017','hourly_2017']
        queries=[s for s in (ROOT/'sql/queries.sql').read_text().split(';') if s.strip()]
        assert len(queries)==len(names)
        for name,query in zip(names,queries):
            pd.read_sql_query(query,con).to_csv(ROOT/'results'/f'{name}.csv',index=False);logger.info('Saved result %s',name)
    logger.info('Raw records=%s; unique hourly records=%s',len(raw),len(hourly))
if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(name)s %(message)s',handlers=[logging.StreamHandler(),logging.FileHandler(ROOT/'results/part1.log')])
    try:run()
    except (OSError,ValueError,sqlite3.Error):logger.error('Part 1 analysis failed',exc_info=True);sys.exit(1)
