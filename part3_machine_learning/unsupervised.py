"""Traffic-condition clustering and exhaustive small categorical association rules."""
import logging,itertools,json
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from config import ROOT,SEED,WEATHERS
logger=logging.getLogger(__name__)

def cluster_inputs(df):
    hour=df.date_time.dt.hour
    # Explicit ordinal project severity, not calibrated physical hazard.
    severity=df.weather_main.map({w:len(WEATHERS)-i for i,w in enumerate(WEATHERS)}).fillna(0)
    return pd.DataFrame({'hour_sin':np.sin(2*np.pi*hour/24),'hour_cos':np.cos(2*np.pi*hour/24),
                         'weather_severity':severity,'traffic_volume':df.traffic_volume},index=df.index)

def run_unsupervised(df):
    train=df.split.eq('train');c=cluster_inputs(df)
    scaler=StandardScaler().fit(c.loc[train]);a=scaler.transform(c.loc[train])
    sample=np.random.default_rng(SEED).choice(len(a),min(2000,len(a)),replace=False)
    candidates=[];fitted={}
    for k in [3,4,5]:
        model=KMeans(n_clusters=k,n_init=10,random_state=SEED).fit(a)
        score=silhouette_score(a[sample],model.predict(a[sample]))
        candidates.append({'k':k,'training_sample_silhouette':score});fitted[k]=model
        logger.info('K-means k=%d silhouette=%.4f',k,score)
    best=max(candidates,key=lambda x:x['training_sample_silhouette'])['k'];model=fitted[best]
    labels=model.predict(scaler.transform(c))
    data=df.copy();data['cluster']=labels
    profiles=data.loc[train].groupby('cluster').agg(n=('traffic_volume','size'),mean_volume=('traffic_volume','mean'),
        mean_hour=('hour','mean'),weekend_share=('day_type',lambda x:float(x.eq('Weekend').mean())),
        mean_temp=('temp','mean'),modal_weather=('weather_main',lambda x:x.mode().iloc[0]))
    ordered=profiles.sort_values('mean_volume').index.tolist()
    descriptors=['Quiet traffic','Moderate traffic','Busy traffic','Very busy traffic','Peak traffic']
    names={int(cluster):f'{descriptors[round(rank*4/(best-1))]} cluster {cluster}' for rank,cluster in enumerate(ordered)}
    profiles['name']=[names[int(i)] for i in profiles.index]
    profiles.to_csv(ROOT/'outputs/cluster_profiles.csv')
    data.loc[df.split.eq('test')].groupby('cluster').agg(n=('traffic_volume','size'),mean_volume=('traffic_volume','mean')).to_csv(ROOT/'outputs/test_cluster_profiles.csv')
    pd.DataFrame(candidates).to_csv(ROOT/'outputs/cluster_selection.csv',index=False)
    joblib.dump({'scaler':scaler,'model':model,'names':names},ROOT/'models/kmeans.joblib',compress=3)
    data[['date_time','split','cluster','traffic_volume','hour']].to_csv(ROOT/'outputs/cluster_assignments.csv',index=False)
    rules=mine_rules(df.loc[train],df.loc[df.split.eq('test')])
    return profiles,rules

def mine_rules(train,test):
    """Enumerate antecedents with 1–3 distinct categorical fields; congestion only as consequent."""
    fields=['time_period','day_type','weather_main'];rows=[]
    target_prior=train.congestion_category.value_counts(normalize=True)
    test_prior=test.congestion_category.value_counts(normalize=True)
    for size in [1,2,3]:
        for cols in itertools.combinations(fields,size):
            # Explicitly enumerate supported antecedents and all observed target buckets.
            for key,group in train.groupby(list(cols),observed=True):
                key=key if isinstance(key,tuple) else (key,)
                if len(group)<50:continue
                mask=pd.Series(True,index=test.index)
                for col,value in zip(cols,key):mask &= test[col].eq(value)
                holdout=test.loc[mask]
                for category,count in group.congestion_category.value_counts().items():
                    support=count/len(train)
                    if count<30 or support<.005:continue
                    confidence=count/len(group);lift=confidence/target_prior[category]
                    if lift<=1:continue
                    hc=int(holdout.congestion_category.eq(category).sum())
                    hconf=hc/len(holdout) if len(holdout) else np.nan
                    rows.append({'antecedent':' AND '.join(f'{col}={value}' for col,value in zip(cols,key)),
                        'consequent':f'congestion={category}','support':support,'confidence':confidence,'lift':lift,
                        'antecedent_n':len(group),'joint_n':int(count),'test_antecedent_n':len(holdout),
                        'test_confidence':hconf,'test_lift':hconf/test_prior[category] if test_prior.get(category,0)>0 else np.nan})
    result=pd.DataFrame(rows).sort_values(['lift','support'],ascending=False)
    result.to_csv(ROOT/'outputs/association_rules.csv',index=False)
    result.head(20).to_csv(ROOT/'outputs/top_association_rules.csv',index=False)
    logger.info('Mined %d supported rules; sorted by TRAINING lift; holdout metrics diagnostic only',len(result))
    return result
