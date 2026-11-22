import argparse,logging,pandas as pd
from pathlib import Path
logger=logging.getLogger(__name__)
def recommend(day_type='weekday',weather='Clear'):
 df=pd.read_csv(Path(__file__).resolve().parents[1]/'data/processed/traffic_clean.csv',parse_dates=['date_time']); weekend=df.date_time.dt.dayofweek>=5; mask=(weekend if day_type.lower()=='weekend' else ~weekend)&df.weather_main.str.casefold().eq(weather.casefold()); g=df[mask].assign(hour=df.loc[mask,'date_time'].dt.hour).groupby('hour').traffic_volume.mean();
 if g.empty: return f'No historical observations for {day_type} and {weather} weather.'
 h=int(g.idxmin()); return f'For a {day_type} journey in {weather} weather, consider travelling between {h:02d}:00 and {(h+1)%24:02d}:00, when historical traffic averaged {g.min():.0f} vehicles per hour.'
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--day-type',choices=['weekday','weekend'],default='weekday'); p.add_argument('--weather',default='Clear'); a=p.parse_args(); logger.info('Recommendation request %s',vars(a)); print(recommend(a.day_type,a.weather))
