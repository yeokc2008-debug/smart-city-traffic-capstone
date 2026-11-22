import logging,matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
logger=logging.getLogger(__name__)
def create_figures(df,out):
 out.mkdir(parents=True,exist_ok=True); paths=[]
 specs=[('hourly_traffic',df.groupby('hour').traffic_volume.mean(),'Average traffic by hour','Hour','Vehicles'),('weekday_weekend',df.groupby('is_weekend').traffic_volume.mean().rename(index={0:'Weekday',1:'Weekend'}),'Weekday vs weekend traffic','','Vehicles'),('weather_traffic',df.groupby('weather_description').traffic_volume.mean().sort_values().tail(10),'Top weather descriptions by average traffic','','Vehicles')]
 for name,series,title,xl,yl in specs:
  fig,ax=plt.subplots(figsize=(8,4.5)); series.plot(kind='bar',ax=ax,color='#2878B5'); ax.set(title=title,xlabel=xl,ylabel=yl); fig.tight_layout(); p=out/f'{name}.png'; fig.savefig(p,dpi=160); plt.close(fig); paths.append(p); logger.info('Saved figure: %s',p)
 fig,ax=plt.subplots(figsize=(7,4.5)); sample=df.sample(min(5000,len(df)),random_state=42); ax.scatter(sample.temp_c,sample.traffic_volume,s=7,alpha=.25); ax.set(title='Temperature and traffic volume',xlabel='Temperature (°C)',ylabel='Vehicles'); fig.tight_layout(); p=out/'temperature_scatter.png'; fig.savefig(p,dpi=160); plt.close(fig); paths.append(p); logger.info('Saved figure: %s',p)
 return paths
