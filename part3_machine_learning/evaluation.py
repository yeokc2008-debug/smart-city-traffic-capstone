"""Evaluation figures and condition-based error slices, with denominators."""
import logging
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay,confusion_matrix,precision_recall_curve,roc_curve,mean_absolute_error
from config import ROOT
logger=logging.getLogger(__name__)

def save(fig,name):
    fig.tight_layout();path=ROOT/'outputs/figures'/name
    fig.savefig(path,dpi=140,bbox_inches='tight');plt.close(fig)
    logger.info('Figure saved %s',path)

def evaluate_outputs(df,results,models,selection,predictions):
    reg=results.loc[results.task.eq('regression')]
    fig,ax=plt.subplots(figsize=(8,4));pos=np.arange(len(reg));ax.bar(pos-.18,reg.validation_mae,.36,label='2017 validation');ax.bar(pos+.18,reg.test_mae,.36,label='2018 test')
    ax.set(xticks=pos,xticklabels=reg.model,title='Demand prediction errors',ylabel='MAE in vehicles per observed hour');ax.legend();save(fig,'01_regression_errors.png')
    test=df.split.eq('test');y=df.loc[test,'high_risk'];fig,ax=plt.subplots(figsize=(8,4.5))
    for name in results.loc[results.task.eq('classification'),'model']:
        p,r,_=precision_recall_curve(y,predictions[name]);ax.plot(r,p,label=name)
    ax.axhline(y.mean(),color='grey',ls='--',label=f'Prevalence {y.mean():.3f}')
    ax.set(title='Proxy label precision recall curves on 2018',xlabel='Recall',ylabel='Precision');ax.legend();save(fig,'02_precision_recall.png')
    cls=selection['classification'];pred=predictions[cls].to_numpy()>=selection['threshold']
    fig,ax=plt.subplots(figsize=(5,4));ConfusionMatrixDisplay(confusion_matrix(y,pred),display_labels=['Proxy 0','Proxy 1']).plot(ax=ax,colorbar=False)
    ax.set_title('Proxy classification at validation selected threshold');save(fig,'03_confusion_matrix.png')
    fig,ax=plt.subplots(figsize=(9,4))
    hist=pd.read_csv(ROOT/'outputs/neural_training_history.csv');ax.plot(hist.epoch,hist.validation_mae)
    ax.set(title='Neural network chronological validation',xlabel='Epoch',ylabel='2017 validation MAE');save(fig,'04_neural_history.png')
    assignments=pd.read_csv(ROOT/'outputs/cluster_assignments.csv')
    fig,ax=plt.subplots(figsize=(8,4.5))
    for cluster,g in assignments.loc[assignments.split.eq('train')].groupby('cluster'):
        sample=g.sample(min(600,len(g)),random_state=42)
        ax.scatter(sample.hour,sample.traffic_volume,s=7,alpha=.25,label=f'Cluster {cluster}')
    ax.set(title='Training traffic condition clusters',xlabel='Local hour',ylabel='Vehicles per observed hour');ax.legend(markerscale=3);save(fig,'05_traffic_clusters.png')
    data=df.loc[test].copy();data['classification_prediction']=pred
    data['regression_prediction']=predictions[selection['regression']].to_numpy()
    data['period']=np.where(data.hour.between(6,19),'Daytime','Night')
    rows=[]
    for field in ['day_type','weather_main','period']:
        for value,g in data.groupby(field,observed=True):
            actual=g.high_risk.to_numpy().astype(bool);prediction=g.classification_prediction.to_numpy().astype(bool)
            tp=int((actual & prediction).sum());fp=int((~actual & prediction).sum());positives=int(actual.sum());negatives=len(g)-positives
            rows.append({'dimension':field,'group':value,'n':len(g),'positives':positives,'predicted_positives':int(prediction.sum()),
                'regression_mae':mean_absolute_error(g.traffic_volume,g.regression_prediction),
                'recall':tp/positives if positives else np.nan,'precision':tp/(tp+fp) if tp+fp else np.nan,
                'false_positive_rate':fp/negatives if negatives else np.nan,'small_group':len(g)<30})
    pd.DataFrame(rows).to_csv(ROOT/'outputs/fairness_slices.csv',index=False)
    return pd.DataFrame(rows)
