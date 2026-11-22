import json,logging,time
from pathlib import Path
import joblib,pandas as pd,numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression,LogisticRegression
from sklearn.ensemble import RandomForestRegressor,RandomForestClassifier
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error,r2_score,accuracy_score,precision_score,recall_score,f1_score,roc_auc_score
logger=logging.getLogger(__name__); logging.basicConfig(level=logging.INFO,format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
ROOT=Path(__file__).resolve().parents[1]; OUT=Path(__file__).parent; MODEL=OUT/'models'; MODEL.mkdir(exist_ok=True); TRACK=OUT/'mlruns'; TRACK.mkdir(exist_ok=True)
df=pd.read_csv(ROOT/'data/processed/traffic_clean.csv',parse_dates=['date_time']); df['hour']=df.date_time.dt.hour; df['dow']=df.date_time.dt.dayofweek; df['hour_sin']=np.sin(2*np.pi*df.hour/24); df['hour_cos']=np.cos(2*np.pi*df.hour/24); df['dow_sin']=np.sin(2*np.pi*df.dow/7); df['dow_cos']=np.cos(2*np.pi*df.dow/7); df['is_holiday']=(df.holiday!='None').astype(int); df['low_visibility']=df.weather_main.isin(['Fog','Mist','Haze','Smoke']).astype(int)
q=df.traffic_volume.quantile([.25,.5,.75]).values; cat=pd.cut(df.traffic_volume,[-np.inf,*q,np.inf],labels=['Low','Medium','High','Severe']); df['high_risk']=(cat.isin(['High','Severe']) & (df.weather_main.isin(['Thunderstorm','Snow','Squall'])|df.low_visibility.eq(1))).astype(int)
features=['temp','rain_1h','snow_1h','clouds_all','hour_sin','hour_cos','dow_sin','dow_cos','is_holiday','weather_main']; num=features[:-1]; pre=ColumnTransformer([('num',StandardScaler(),num),('cat',OneHotEncoder(handle_unknown='ignore'),['weather_main'])]); train,test=train_test_split(np.arange(len(df)),test_size=.2,random_state=42)
results=[]
for name,est in [('linear_regression',LinearRegression()),('random_forest_regression',RandomForestRegressor(n_estimators=80,max_depth=16,n_jobs=-1,random_state=42)),('neural_network_regression',MLPRegressor(hidden_layer_sizes=(32,16),max_iter=120,early_stopping=True,random_state=42))]:
 model=Pipeline([('prep',pre),('model',est)]); t=time.time(); model.fit(df.loc[train,features],df.loc[train,'traffic_volume']); pred=model.predict(df.loc[test,features]); m={'model':name,'task':'regression','mae':mean_absolute_error(df.loc[test,'traffic_volume'],pred),'r2':r2_score(df.loc[test,'traffic_volume'],pred),'seconds':time.time()-t}; results.append(m); joblib.dump(model,MODEL/f'{name}.joblib'); logger.info('%s %s',name,m)
for name,est in [('logistic_classification',LogisticRegression(max_iter=500,class_weight='balanced')),('random_forest_classification',RandomForestClassifier(n_estimators=80,max_depth=14,class_weight='balanced',n_jobs=-1,random_state=42))]:
 model=Pipeline([('prep',pre),('model',est)]); model.fit(df.loc[train,features],df.loc[train,'high_risk']); pred=model.predict(df.loc[test,features]); prob=model.predict_proba(df.loc[test,features])[:,1]; y=df.loc[test,'high_risk']; m={'model':name,'task':'classification','accuracy':accuracy_score(y,pred),'precision':precision_score(y,pred,zero_division=0),'recall':recall_score(y,pred,zero_division=0),'f1':f1_score(y,pred,zero_division=0),'roc_auc':roc_auc_score(y,prob)}; results.append(m); joblib.dump(model,MODEL/f'{name}.joblib'); logger.info('%s %s',name,m)
pd.DataFrame(results).to_csv(OUT/'model_results.csv',index=False); (TRACK/'experiments.json').write_text(json.dumps(results,indent=2));
# Model-agnostic permutation importance is supplied as the explainability fallback because SHAP is optional.
from sklearn.inspection import permutation_importance
best=joblib.load(MODEL/'random_forest_regression.joblib'); pi=permutation_importance(best,df.loc[test[:3000],features],df.loc[test[:3000],'traffic_volume'],n_repeats=3,random_state=42,n_jobs=-1); pd.DataFrame({'feature':features,'importance':pi.importances_mean}).sort_values('importance',ascending=False).to_csv(OUT/'explainability_permutation.csv',index=False)
