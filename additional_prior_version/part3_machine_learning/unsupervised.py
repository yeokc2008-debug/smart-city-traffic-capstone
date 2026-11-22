import logging,pandas as pd,numpy as np
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
logging.basicConfig(level=logging.INFO); logger=logging.getLogger(__name__); ROOT=Path(__file__).resolve().parents[1]; O=Path(__file__).parent
df=pd.read_csv(ROOT/'data/processed/traffic_clean.csv',parse_dates=['date_time']); df['hour']=df.date_time.dt.hour; df['weather_severity']=df.weather_main.map({'Clear':0,'Clouds':1,'Mist':2,'Haze':2,'Fog':3,'Rain':3,'Drizzle':3,'Snow':4,'Thunderstorm':5,'Squall':5,'Smoke':4}).fillna(2)
cols=['hour','weather_severity','traffic_volume']; z=StandardScaler().fit_transform(df[cols]); km=KMeans(n_clusters=4,n_init=10,random_state=42).fit(z); df['cluster']=km.labels_; df.groupby('cluster')[cols].agg(['mean','count']).to_csv(O/'cluster_profiles.csv'); logger.info('Saved four traffic-condition cluster profiles')
df['period']=pd.cut(df.hour,[-1,5,9,15,19,23],labels=['Night','AM peak','Midday','PM peak','Late']); df['week_type']=np.where(df.date_time.dt.dayofweek>=5,'Weekend','Weekday'); df['congested']=df.traffic_volume.gt(5500)
rows=[]
for c in ['period','week_type','weather_main']:
 for v,g in df.groupby(c,observed=True):
  support=len(g)/len(df); conf=g.congested.mean(); base=df.congested.mean(); rows.append({'antecedent':f'{c}={v}','support':support,'confidence_congestion':conf,'lift':conf/base if base else np.nan})
pd.DataFrame(rows).sort_values('lift',ascending=False).to_csv(O/'association_rules.csv',index=False)
