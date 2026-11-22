"""Headless Matplotlib figures with explicit units and observed-hour scope."""
import logging
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
logger = logging.getLogger(__name__)

def make_figures(df, output_dir):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.size':10, 'axes.spines.top':False, 'axes.spines.right':False,
                         'figure.facecolor':'white','axes.titleweight':'bold'})
    def save(fig, name):
        fig.tight_layout()
        path=out/name
        fig.savefig(path, dpi=160, bbox_inches='tight')
        plt.close(fig)
        logger.info('Figure saved: %s', path)
    fig, ax = plt.subplots(figsize=(9,4.8))
    for weekend, label, color in [(0,'Weekday','#145da0'),(1,'Weekend','#d46a1a')]:
        s=df.loc[df.is_weekend.eq(weekend)].groupby('hour').traffic_volume.mean()
        ax.plot(s.index,s.values,label=label,color=color,marker='o',markersize=3)
    ax.set(title='Hourly traffic by day type',xlabel='Local hour of day',ylabel='Mean vehicles per observed hour',xticks=range(0,24,2))
    ax.legend(frameon=False);ax.grid(alpha=.2)
    save(fig,'01_hourly_day_type.png')
    fig, ax = plt.subplots(figsize=(9,4.8))
    g=df.groupby('weather_main').traffic_volume.agg(['mean','size']).sort_values('mean')
    ax.barh(g.index,g['mean'],color=['#d46a1a' if n<30 else '#145da0' for n in g['size']])
    for y,(_,r) in enumerate(g.iterrows()):
        ax.text(r['mean']+35,y,f'n={int(r["size"]):,}',va='center',fontsize=8)
    ax.set(title='Traffic by selected weather condition',xlabel='Mean vehicles per observed hour',xlim=(0,g['mean'].max()*1.3))
    save(fig,'02_weather_traffic.png')
    fig, ax=plt.subplots(figsize=(9,4.8))
    image=ax.hexbin(df.temp_c,df.traffic_volume,gridsize=45,mincnt=1,cmap='viridis',bins='log')
    fig.colorbar(image,ax=ax,label='Observed hours per hexagon on log colour scale')
    ax.set(title='Temperature and traffic volume',xlabel='Temperature in degrees Celsius',ylabel='Vehicles per observed hour')
    save(fig,'03_temperature_traffic.png')
    fig, ax=plt.subplots(figsize=(9,4.8))
    ax.hist(df.traffic_volume,bins=45,color='#145da0',edgecolor='white')
    for q,label,color in [(.5,'Median','#d46a1a'),(.75,'Third quartile','#843c8c')]:
        value=df.traffic_volume.quantile(q)
        ax.axvline(value,color=color,label=f'{label}: {value:,.0f}',linestyle='--')
    ax.set(title='Distribution of observed hourly traffic',xlabel='Vehicles per observed hour',ylabel='Number of observed hours')
    ax.legend(frameon=False)
    save(fig,'04_traffic_distribution.png')
