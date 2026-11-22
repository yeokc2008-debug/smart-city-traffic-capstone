import logging
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
logger=logging.getLogger(__name__)
ROOT=Path(__file__).resolve().parents[1]
def run():
 d=pd.read_csv(ROOT/'data/Traffic_PowerBI_Ready.csv',parse_dates=['date_time']);out=ROOT/'charts'
 fig,axes=plt.subplots(3,1,figsize=(10,7),sharex=True)
 for year,ax in zip([2015,2016,2017],axes):
  x=d.loc[d.Year.eq(year)].set_index('date_time').traffic_volume.resample('D').mean();ax.plot(x.index.dayofyear,x,color='#176b87',linewidth=1);ax.set(ylabel=str(year),ylim=(0,6500));ax.grid(alpha=.15)
 axes[-1].set(xlabel='Day of year',xlim=(1,366));fig.suptitle('Daily average traffic by year\nMissing days remain gaps; vehicles per observed hour');fig.tight_layout();fig.savefig(out/'daily_2015_2017.png',dpi=150);plt.close(fig)
 h=d[d.Year.eq(2017)].groupby('Hour').traffic_volume.mean();fig,ax=plt.subplots(figsize=(9,4));h.plot.bar(ax=ax,color='#176b87');ax.set(title='Average hourly traffic in 2017',xlabel='Hour',ylabel='Vehicles per observed hour');fig.tight_layout();fig.savefig(out/'hourly_2017.png',dpi=150);plt.close(fig)
 w=d.groupby('weather_main').traffic_volume.agg(['mean','count']).sort_values('mean');fig,ax=plt.subplots(figsize=(9,5));ax.barh(w.index,w['mean'],color='#176b87');ax.set(title='Average traffic by primary hourly weather',xlabel='Vehicles per observed hour');
 for i,(_,r) in enumerate(w.iterrows()):ax.text(r['mean']+30,i,f'n={int(r["count"]):,}',va='center',fontsize=8)
 ax.set_xlim(0,5500);fig.tight_layout();fig.savefig(out/'weather_hourly.png',dpi=150);plt.close(fig)
 fig,ax=plt.subplots(figsize=(9,5));plot=ax.hexbin(d['Temperature Celsius'],d.traffic_volume,gridsize=55,mincnt=1,cmap='Blues');fig.colorbar(plot,ax=ax,label='Observed-hour count');ax.set(title='Temperature and hourly traffic',xlabel='Temperature Celsius',ylabel='Vehicles per observed hour');fig.tight_layout();fig.savefig(out/'temperature_traffic.png',dpi=150);plt.close(fig)
 logger.info('Four task-specific figures saved')
if __name__=='__main__':run()
