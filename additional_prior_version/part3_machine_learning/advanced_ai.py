import logging,pandas as pd
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
logging.basicConfig(level=logging.INFO); logger=logging.getLogger(__name__)
ROOT=Path(__file__).resolve().parents[1]; df=pd.read_csv(ROOT/'data/processed/traffic_clean.csv',parse_dates=['date_time']); df['hour']=df.date_time.dt.hour
cols=['temp','rain_1h','snow_1h','clouds_all','traffic_volume','hour']; x=StandardScaler().fit_transform(df[cols]); model=IsolationForest(contamination=.01,random_state=42,n_jobs=-1).fit(x); df['anomaly_score']=model.decision_function(x); df['is_anomaly']=(model.predict(x)==-1).astype(int)
df.nsmallest(500,'anomaly_score')[['date_time',*cols,'anomaly_score','is_anomaly']].to_csv(Path(__file__).parent/'anomalies.csv',index=False); logger.info('Self-supervised anomaly detection identified %d records',df.is_anomaly.sum())
