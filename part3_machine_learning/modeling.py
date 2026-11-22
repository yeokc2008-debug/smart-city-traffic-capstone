"""Chronological model evaluation and a manually validation-stopped neural network."""
import logging,copy,time,json,os
os.environ.setdefault('MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING','false')
os.environ.setdefault('MLFLOW_DISABLE_TELEMETRY','true')
os.environ.setdefault('MLFLOW_DISABLE_AGENT_HINT','true')
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge,LogisticRegression
from sklearn.ensemble import RandomForestRegressor,RandomForestClassifier
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (mean_absolute_error,r2_score,accuracy_score,precision_score,recall_score,
                             f1_score,roc_auc_score,average_precision_score,precision_recall_curve)
from config import ROOT,SEED
logger=logging.getLogger(__name__)

class DenseDemandModel:
    """Three hidden layers, training-only scalers and explicit chronological validation."""
    def fit(self,x,y,x_val,y_val,max_epochs=100,patience=12):
        self.columns=list(x.columns)
        self.x_scaler=StandardScaler().fit(x)
        self.y_scaler=StandardScaler().fit(np.asarray(y).reshape(-1,1))
        a=self.x_scaler.transform(x);b=self.y_scaler.transform(np.asarray(y).reshape(-1,1)).ravel()
        v=self.x_scaler.transform(x_val)
        self.net=MLPRegressor(hidden_layer_sizes=(64,32,16),activation='relu',solver='adam',
                              batch_size=256,learning_rate_init=.001,alpha=.01,shuffle=False,
                              early_stopping=False,random_state=SEED)
        best=float('inf');best_net=None;stale=0;rows=[]
        for epoch in range(1,max_epochs+1):
            self.net.partial_fit(a,b)
            prediction=self.y_scaler.inverse_transform(self.net.predict(v).reshape(-1,1)).ravel().clip(0)
            error=mean_absolute_error(y_val,prediction)
            rows.append({'epoch':epoch,'training_loss_standardised':float(self.net.loss_),'validation_mae':error})
            logger.debug('Neural epoch %d validation MAE %.3f',epoch,error)
            if error<best-1:
                best=error;best_net=copy.deepcopy(self.net);self.best_epoch=epoch;stale=0
            else:stale+=1
            if stale>=patience:break
        self.net=best_net;self.history=rows
        logger.info('Neural network finished %d epochs; retained epoch %d',len(rows),self.best_epoch)
        return self
    def predict(self,x):
        a=self.x_scaler.transform(x[self.columns])
        return self.y_scaler.inverse_transform(self.net.predict(a).reshape(-1,1)).ravel().clip(0)

def classification_metrics(y,score,threshold):
    pred=np.asarray(score)>=threshold
    return {'accuracy':accuracy_score(y,pred),'precision':precision_score(y,pred,zero_division=0),
            'recall':recall_score(y,pred,zero_division=0),'f1':f1_score(y,pred,zero_division=0),
            'roc_auc':roc_auc_score(y,score) if len(np.unique(y))==2 else float('nan'),
            'pr_auc_average_precision':average_precision_score(y,score) if np.sum(y)>0 else float('nan')}

def choose_threshold(y,score):
    p,r,t=precision_recall_curve(y,score)
    f=2*p[:-1]*r[:-1]/np.maximum(p[:-1]+r[:-1],1e-12)
    return float(t[int(np.argmax(f))])

def configure_tracking():
    import mlflow
    mlflow.set_tracking_uri('sqlite:///'+str(ROOT/'mlflow.db'))
    client=mlflow.MlflowClient()
    name='Capstone_Part3_Mobility'
    exp=client.get_experiment_by_name(name)
    if exp is None:
        exp_id=client.create_experiment(name,artifact_location=(ROOT/'mlartifacts').as_uri())
    else:exp_id=exp.experiment_id
    mlflow.set_experiment(experiment_id=exp_id)
    return mlflow,client

def train_models(df,x):
    mlflow,client=configure_tracking()
    train=df.split.eq('train');valid=df.split.eq('validation');test=df.split.eq('test')
    specs=[('ridge_v1','regression',make_pipeline(StandardScaler(),Ridge(alpha=10))),
           ('forest_reg_v2','regression',make_pipeline(StandardScaler(),RandomForestRegressor(n_estimators=100,max_depth=14,min_samples_leaf=3,random_state=SEED,n_jobs=2))),
           ('logistic_v1','classification',make_pipeline(StandardScaler(),LogisticRegression(C=1,max_iter=1000,class_weight='balanced',random_state=SEED))),
           ('forest_cls_v2','classification',make_pipeline(StandardScaler(),RandomForestClassifier(n_estimators=100,max_depth=12,min_samples_leaf=4,class_weight='balanced_subsample',random_state=SEED,n_jobs=2))),
           ('neural_v3','regression',DenseDemandModel())]
    rows=[];predictions=df.loc[test,['date_time','traffic_volume','high_risk','weather_main','day_type','hour']].copy()
    models={};manifest=[]
    for name,task,model in specs:
        y=df.high_risk if task=='classification' else df.traffic_volume
        start=time.perf_counter()
        if isinstance(model,DenseDemandModel):
            model.fit(x.loc[train],y.loc[train],x.loc[valid],y.loc[valid])
            pd.DataFrame(model.history).to_csv(ROOT/'outputs/neural_training_history.csv',index=False)
        else:model.fit(x.loc[train],y.loc[train])
        elapsed=time.perf_counter()-start
        if task=='classification':
            vs=model.predict_proba(x.loc[valid])[:,1];ts=model.predict_proba(x.loc[test])[:,1]
            threshold=choose_threshold(y.loc[valid],vs)
            vm=classification_metrics(y.loc[valid],vs,threshold);tm=classification_metrics(y.loc[test],ts,threshold)
        else:
            vs=model.predict(x.loc[valid]).clip(0);ts=model.predict(x.loc[test]).clip(0);threshold=None
            vm={'mae':mean_absolute_error(y.loc[valid],vs),'r2':r2_score(y.loc[valid],vs)}
            tm={'mae':mean_absolute_error(y.loc[test],ts),'r2':r2_score(y.loc[test],ts)}
        path=ROOT/'models'/f'{name}.joblib';joblib.dump(model,path,compress=3)
        registry='TrafficVolume' if task=='regression' else 'ProxyRisk'
        with mlflow.start_run(run_name=name) as run:
            mlflow.log_params({'algorithm':type(model).__name__,'model_id':name,'task':task,
                               'train_through':'2016','validation_year':'2017','test_year':'2018',
                               'seed':SEED,'predictor_count':x.shape[1],'proxy_threshold':3427,
                               'network_architecture':'64,32,16' if name=='neural_v3' else 'not_applicable'})
            if hasattr(model,'get_params'):
                params={k:str(v)[:200] for k,v in model.get_params().items() if k.startswith(('ridge__','randomforest','logistic'))}
                mlflow.log_params(params)
            if threshold is not None:mlflow.log_param('validation_selected_threshold',threshold)
            mlflow.log_metrics({**{'validation_'+k:float(v) for k,v in vm.items()},**{'test_'+k:float(v) for k,v in tm.items()},
                                'training_seconds':elapsed,'model_bytes':path.stat().st_size})
            mlflow.log_artifact(str(path),artifact_path='models')
            mlflow.log_dict({'feature_columns':list(x.columns),'label':'documented proxy; not actual accidents'},'feature_schema.json')
            existing=client.search_registered_models(filter_string=f"name='{registry}'")
            if not existing:client.create_registered_model(registry)
            version=client.create_model_version(registry,source=f'runs:/{run.info.run_id}/models/{path.name}',run_id=run.info.run_id)
            client.set_model_version_tag(registry,version.version,'model_id',name)
            client.set_model_version_tag(registry,version.version,'serialization','joblib artifact; not MLflow pyfunc')
            manifest.append({'model_id':name,'task':task,'registry':registry,'version':version.version,'run_id':run.info.run_id,
                             'artifact':str(path.relative_to(ROOT)),'threshold':threshold,'training_seconds':elapsed})
        rows.append({'model':name,'task':task,'training_seconds':elapsed,'model_bytes':path.stat().st_size,
                     'threshold':threshold,**{'validation_'+k:v for k,v in vm.items()},**{'test_'+k:v for k,v in tm.items()}})
        predictions[name]=ts
        models[name]=model
        logger.info('Trained %s in %.2fs; validation=%s; test=%s',name,elapsed,vm,tm)
    results=pd.DataFrame(rows)
    reg=results.loc[results.task.eq('regression')].sort_values('validation_mae').iloc[0]['model']
    cls=results.loc[results.task.eq('classification')].sort_values('validation_pr_auc_average_precision',ascending=False).iloc[0]['model']
    threshold=float(results.loc[results.model.eq(cls),'threshold'].iloc[0])
    selection={'regression':reg,'classification':cls,'threshold':threshold,'selection_scope':'2017 validation only',
               'feature_columns':list(x.columns),'fixed_proxy_median':3427,'classifier_score':'uncalibrated proxy-positive score; not accident probability'}
    results.to_csv(ROOT/'outputs/model_comparison.csv',index=False)
    predictions.to_csv(ROOT/'outputs/test_predictions.csv',index=False)
    (ROOT/'models/selection.json').write_text(json.dumps(selection,indent=2))
    (ROOT/'outputs/model_versions.json').write_text(json.dumps(manifest,indent=2))
    yval=df.loc[valid,'traffic_volume']
    valpred=models[reg].predict(x.loc[valid]).clip(0)
    pd.DataFrame({'actual':yval,'predicted':valpred}).to_csv(ROOT/'outputs/validation_regression.csv',index=False)
    logger.info('Selected regression=%s and classification=%s using validation only',reg,cls)
    return results,models,selection,predictions
