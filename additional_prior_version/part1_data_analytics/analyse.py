from pathlib import Path
import json,sqlite3,pandas as pd,numpy as np
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'data'; O=Path(__file__).parent/'outputs'; O.mkdir(exist_ok=True)
df=pd.read_csv(D/'Metro_Interstate_Traffic_Volume.csv'); df['holiday']=df.holiday.fillna('None'); df['date_time']=pd.to_datetime(df.date_time)
con=sqlite3.connect(O/'traffic.db'); df.to_sql('traffic',con,if_exists='replace',index=False)
annual=df.assign(year=df.date_time.dt.year).query('2012<=year<=2017').groupby('year').traffic_volume.sum().to_frame('total_volume'); annual['change']=annual.total_volume.diff(); annual['pct_change']=annual.total_volume.pct_change()*100
annual.to_csv(O/'annual_trends.csv')
holiday=df[df.date_time.dt.year.isin([2015,2016,2017]) & df.holiday.isin(["New Years Day","Labor Day"])].assign(year=df.date_time.dt.year).groupby(['year','holiday']).agg(avg_temp_k=('temp','mean'),avg_traffic=('traffic_volume','mean'),hours=('traffic_volume','size')).reset_index(); holiday.to_csv(O/'holiday_temperature.csv',index=False)
s=df.traffic_volume; stats=pd.Series({'mean':s.mean(),'median':s.median(),'std':s.std(),'variance':s.var(),'range':s.max()-s.min(),'temp_traffic_correlation':df.temp.corr(s)}); stats.to_csv(O/'statistics.csv',header=['value'])
cong=s>5500; clear=df.weather_main.eq('Clear'); hot=df.temp>292; cloudy=df.weather_main.eq('Clouds')
def p(x): return x.mean()
a,b,c,d=((cong&clear).sum(),((~cong)&clear).sum(),(cong&cloudy).sum(),((~cong)&cloudy).sum())
prob=pd.Series({'P_congestion':p(cong),'P_clear':p(clear),'P_congestion_and_clear':p(cong&clear),'P_clear_given_congestion':clear[cong].mean(),'P_hot_given_congestion':hot[cong].mean(),'P_congestion_x_P_clear':p(cong)*p(clear),'independence_gap':p(cong&clear)-p(cong)*p(clear),'odds_ratio_clear_vs_cloudy':(a/b)/(c/d)}); prob.to_csv(O/'probabilities.csv',header=['value'])
weather=df.groupby('weather_main').traffic_volume.agg(['mean','count']).sort_values('mean',ascending=False); weather.to_csv(O/'weather_traffic.csv')
daily=df[df.date_time.dt.year.isin([2015,2016,2017])].set_index('date_time').traffic_volume.resample('D').mean().dropna(); daily.to_csv(O/'daily_average_2015_2017.csv')
hourly=df[df.date_time.dt.year.eq(2017)].assign(hour=df.date_time.dt.hour).groupby('hour').traffic_volume.mean(); hourly.to_csv(O/'hourly_average_2017.csv')
summary={'rows':len(df),'columns':len(df.columns),'annual':annual.round(3).reset_index().to_dict('records'),'stats':stats.round(4).to_dict(),'probabilities':prob.round(6).to_dict(),'highest_weather':weather.index[0],'lowest_weather':weather.index[-1],'weather_difference':float(weather.iloc[0]['mean']-weather.iloc[-1]['mean'])}
(O/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
