import argparse,logging,sys
from pathlib import Path
import pandas as pd
from common import configure
from feature_engineering import engineer
from visualizations import create_figures
logger=logging.getLogger(__name__); EXPECTED={'holiday','temp','rain_1h','snow_1h','clouds_all','weather_main','weather_description','date_time','traffic_volume'}
def load(path):
 try: df=pd.read_csv(path); logger.info('Loaded %d rows and %d columns from %s',*df.shape,path); return df
 except (OSError,pd.errors.ParserError): logger.error('Cannot load input',exc_info=True); raise
def clean(df):
 missing=EXPECTED-set(df.columns)
 if missing: raise ValueError(f'Missing columns: {sorted(missing)}')
 x=df.copy(); x['holiday']=x.holiday.fillna('None').str.strip(); x['weather_main']=x.weather_main.str.strip().str.title(); x['weather_description']=x.weather_description.str.strip().str.lower()
 x['date_time']=pd.to_datetime(x.date_time,errors='coerce'); n=x.date_time.isna().sum()
 if n: logger.warning('Dropped %d rows with invalid date/time',n); x=x.dropna(subset=['date_time'])
 n=x.duplicated().sum()
 if n: logger.warning('Dropped %d exact duplicate rows',n); x=x.drop_duplicates()
 bad_temp=(x.temp<=0)|(x.temp>330); n=bad_temp.sum()
 if n:
  for month in sorted(x.loc[bad_temp,'date_time'].dt.month.unique()):
   mask=bad_temp & x.date_time.dt.month.eq(month); med=x.loc[(~bad_temp)&x.date_time.dt.month.eq(month),'temp'].median(); x.loc[mask,'temp']=med
  logger.warning('Imputed %d impossible temperature values with monthly medians',n)
 bad_rain=(x.rain_1h<0)|(x.rain_1h>9000); n=bad_rain.sum()
 if n: x.loc[bad_rain,'rain_1h']=x.loc[~bad_rain,'rain_1h'].median(); logger.warning('Imputed %d implausible rainfall values',n)
 for c in ['snow_1h','clouds_all','traffic_volume']:
  bad=x[c]<0
  if bad.any(): logger.warning('Imputed %d negative %s values',bad.sum(),c); x.loc[bad,c]=x.loc[~bad,c].median()
 return x.sort_values('date_time').reset_index(drop=True)
def main(path,debug=False):
 configure(logging.DEBUG if debug else logging.INFO)
 try:
  clean_df=clean(load(path)); root=Path(__file__).resolve().parents[1]; d=root/'data'/'processed'; d.mkdir(parents=True,exist_ok=True); clean_df.to_csv(d/'traffic_clean.csv',index=False); logger.info('Saved cleaned data: %s',d/'traffic_clean.csv')
  feat=engineer(clean_df); feat.to_csv(d/'traffic_features.csv',index=False); logger.info('Saved feature data: %s',d/'traffic_features.csv'); create_figures(feat,Path(__file__).parent/'figures')
 except Exception: logger.error('Pipeline failed',exc_info=True); return 1
 return 0
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--input',default='data/Metro_Interstate_Traffic_Volume.csv'); p.add_argument('--debug',action='store_true'); a=p.parse_args(); sys.exit(main(a.input,a.debug))
