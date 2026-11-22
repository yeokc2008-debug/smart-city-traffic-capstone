import argparse,logging,pandas as pd
from pathlib import Path
logger=logging.getLogger(__name__); DATA=Path(__file__).resolve().parents[1]/'data/processed/traffic_features.csv'
def main():
 p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True); sub.add_parser('summary'); q=sub.add_parser('datetime'); q.add_argument('value'); h=sub.add_parser('high-traffic'); h.add_argument('--threshold',type=int,default=5500); sub.add_parser('compare'); a=p.parse_args(); logger.info('CLI command=%s args=%s',a.cmd,vars(a)); df=pd.read_csv(DATA,parse_dates=['date_time'])
 if a.cmd=='summary': print(df.traffic_volume.describe().round(2).to_string())
 elif a.cmd=='datetime':
  try: dt=pd.to_datetime(a.value)
  except Exception: logger.error('Invalid date: %s',a.value); return 2
  print(df.loc[df.date_time.eq(dt),['date_time','weather_description','traffic_volume']].to_string(index=False))
 elif a.cmd=='high-traffic': print(df.nlargest(10,'traffic_volume')[['date_time','traffic_volume']].to_string(index=False))
 else: print(df.groupby('is_weekend').traffic_volume.mean().rename(index={0:'Weekday',1:'Weekend'}).round(1).to_string())
if __name__=='__main__': main()
