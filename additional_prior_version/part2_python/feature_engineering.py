import logging,numpy as np,pandas as pd
logger=logging.getLogger(__name__)
def engineer(df):
 logger.info('Feature engineering input shape: %s',df.shape); x=df.copy(); dt=x.date_time
 x['hour']=dt.dt.hour; x['day_of_week']=dt.dt.dayofweek; x['is_weekend']=(x.day_of_week>=5).astype(int); x['is_holiday']=(x.holiday!='None').astype(int)
 x['hour_sin']=np.sin(2*np.pi*x.hour/24); x['hour_cos']=np.cos(2*np.pi*x.hour/24); x['dow_sin']=np.sin(2*np.pi*x.day_of_week/7); x['dow_cos']=np.cos(2*np.pi*x.day_of_week/7)
 x['temp_c']=x.temp-273.15; x['is_high_temp']=(x.temp>292).astype(int); x['is_low_visibility']=x.weather_main.isin(['Fog','Mist','Haze','Smoke']).astype(int)
 for c in ['temp','clouds_all']:
  sd=x[c].std(); x[c+'_scaled']=(x[c]-x[c].mean())/(sd if sd else 1)
 q=x.traffic_volume.quantile([.25,.5,.75]).values; logger.debug('Congestion quartiles: %s',q)
 x['congestion_category']=pd.cut(x.traffic_volume,[-np.inf,q[0],q[1],q[2],np.inf],labels=['Low','Medium','High','Severe'],include_lowest=True)
 risky=x.weather_main.isin(['Thunderstorm','Snow','Squall']) | x.is_low_visibility.eq(1); x['high_risk']=(x.congestion_category.isin(['High','Severe']) & risky).astype(int)
 x=pd.get_dummies(x,columns=['weather_main'],prefix='weather',dtype=int)
 logger.info('Feature engineering output shape: %s',x.shape); return x
