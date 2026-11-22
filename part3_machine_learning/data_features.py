"""Rebuild hourly data from original bytes with training-period weather imputation."""
import logging,json,hashlib
import numpy as np
import pandas as pd
from config import ROOT,TRAIN_END,VALID_END,WEATHERS,RISK_WEATHER,LABEL_QUARTILES
from part2_cleaning import clean_data
logger=logging.getLogger(__name__)

def build_features(df):
    dt=pd.to_datetime(df['date_time'],errors='raise')
    x=pd.DataFrame(index=df.index)
    x['hour']=dt.dt.hour
    x['day_of_week']=dt.dt.dayofweek
    x['is_weekend']=x.day_of_week.ge(5).astype(int)
    x['is_holiday']=df.holiday.ne('None').astype(int)
    x['temp_c']=pd.to_numeric(df.temp)-273.15
    for name in ['rain_1h','snow_1h','clouds_all']:
        x[name]=pd.to_numeric(df[name])
    for name,values,period in [('hour',dt.dt.hour,24),('dow',dt.dt.dayofweek,7),('month',dt.dt.month-1,12)]:
        x[name+'_sin']=np.sin(2*np.pi*values/period)
        x[name+'_cos']=np.cos(2*np.pi*values/period)
    for name in WEATHERS:
        x['weather_'+name.lower()]=df.weather_main.eq(name).astype(int)
    x['is_low_visibility']=df.weather_main.isin(['Fog','Mist','Haze','Smoke']).astype(int)
    x['is_severe_weather']=df.weather_main.isin(['Thunderstorm','Snow','Squall']).astype(int)
    assert np.isfinite(x.to_numpy()).all()
    return x.astype(float)

def categories(volumes,quartiles=LABEL_QUARTILES):
    a,b,c=quartiles
    return np.select([volumes<=a,volumes<=b,volumes<=c],['Low','Medium','High'],default='Severe')

def load_data():
    source=ROOT/'data/Metro_Interstate_Traffic_Volume.csv.gz'
    raw=pd.read_csv(source,keep_default_na=False)
    logger.info('Raw data loaded %d x %d',*raw.shape)
    df,audit,imputation=clean_data(raw,collapse='severe',fit_end=TRAIN_END)
    df['congestion_category']=categories(df.traffic_volume)
    df['high_risk']=(df.traffic_volume.gt(LABEL_QUARTILES[1]) & df.weather_main.isin(RISK_WEATHER)).astype(int)
    df['day_type']=np.where(df.date_time.dt.dayofweek.ge(5),'Weekend','Weekday')
    df['hour']=df.date_time.dt.hour
    df['time_period']=pd.cut(df.hour,bins=[-1,5,9,15,19,23],labels=['Overnight','Morning','Midday','Evening','Late'])
    df['split']=np.select([df.date_time<=pd.Timestamp(TRAIN_END),df.date_time<=pd.Timestamp(VALID_END)],['train','validation'],default='test')
    x=build_features(df)
    audit.update({'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'fixed_label_quartiles':LABEL_QUARTILES,
                  'computed_full_quartiles':df.traffic_volume.quantile([.25,.5,.75]).tolist(),
                  'train_only_quartiles':df.loc[df.split.eq('train'),'traffic_volume'].quantile([.25,.5,.75]).tolist(),
                  'proxy_positive_hours':int(df.high_risk.sum()),'imputation_fit_end':TRAIN_END})
    out=ROOT/'outputs';out.mkdir(exist_ok=True)
    df.to_csv(ROOT/'data/traffic_hourly.csv',index=False)
    (out/'data_audit.json').write_text(json.dumps({'audit':audit,'imputation':imputation,'predictors':x.columns.tolist()},indent=2))
    df.groupby('split',sort=False).agg(hours=('traffic_volume','size'),positives=('high_risk','sum'),
                                    start=('date_time','min'),end=('date_time','max')).to_csv(out/'split_summary.csv')
    logger.info('Prepared %d observed hours; proxy positives %d; feature count %d',len(df),df.high_risk.sum(),x.shape[1])
    return df,x
