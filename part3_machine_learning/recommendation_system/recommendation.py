"""Single-corridor travel-window recommendation, with support counts and explicit assumptions."""
import logging,json
import pandas as pd
import numpy as np
import joblib
from config import ROOT,RISK_WEATHER,WEATHERS
from data_features import build_features
logger=logging.getLogger(__name__)

def recommend(date,weather='Clear',start=7,end=12,is_holiday=False):
    stamp=pd.to_datetime(date,format='%Y-%m-%d',errors='raise')
    if weather not in WEATHERS[:-1] or not 0<=start<end<=24:
        raise ValueError('Use a known weather and a window 0 <= start < end <= 24')
    df=pd.read_csv(ROOT/'data/traffic_hourly.csv',keep_default_na=False,parse_dates=['date_time'])
    df=df.loc[df.split.eq('train')].copy()
    day_type='Weekend' if stamp.dayofweek>=5 else 'Weekday'
    selected=json.loads((ROOT/'models/selection.json').read_text())
    model=joblib.load(ROOT/'models'/f'{selected["regression"]}.joblib')
    rows=[];inputs=[]
    for hour in range(start,end):
        support=df.loc[df.day_type.eq(day_type)&df.hour.eq(hour)&df.weather_main.eq(weather)]
        scope='day type, hour and weather'
        if len(support)<20:
            support=df.loc[df.day_type.eq(day_type)&df.hour.eq(hour)]
            scope='day type and hour fallback'
            logger.warning('Recommendation hour %d: sparse weather sample; use %d day-type observations',hour,len(support))
        if support.empty:continue
        inputs.append({'date_time':stamp+pd.Timedelta(hours=hour),'holiday':'ProvidedHoliday' if is_holiday else 'None',
            'weather_main':weather,'temp':support.temp.median(),'rain_1h':support.rain_1h.median(),
            'snow_1h':support.snow_1h.median(),'clouds_all':support.clouds_all.median()})
        rows.append({'hour':hour,'historical_mean':float(support.traffic_volume.mean()),'n':len(support),'support_scope':scope})
    if not rows:raise ValueError('No historical support within the permitted window')
    table=pd.DataFrame(rows);table['model_prediction']=model.predict(build_features(pd.DataFrame(inputs))).clip(0)
    table['ranking_score']=.5*table.historical_mean+.5*table.model_prediction
    table=table.sort_values('ranking_score')
    best=table.iloc[0];hour=int(best.hour)
    message=(f'For the {day_type.lower()} journey on {stamp:%Y-%m-%d}, consider {hour:02d}:00–{hour+1:02d}:00 '
             f'within your permitted window. Historical support averages {best.historical_mean:,.0f} vehicles/hour '
             f'(n={int(best.n)}); the demand model estimates {best.model_prediction:,.0f}. '
             f'Weather scenario: {weather}; other weather inputs use historical medians. '
             'This ranks travel timing on one corridor, not alternative routes; lower volume does not guarantee less delay or safer travel.')
    if weather in RISK_WEATHER:
        message+=' Severe/low-visibility weather is present; this is not a safety endorsement.'
    logger.info('Recommendation generated for date=%s weather=%s window=%d–%d',date,weather,start,end)
    return {'recommendation':message,'date':date,'weather':weather,'day_type':day_type,
            'holiday_assumption':bool(is_holiday),'ranking':'equal-weight historical mean and selected model prediction',
            'candidates':table.to_dict(orient='records')}

def save_examples():
    examples=[recommend('2018-06-18','Clear',7,12),recommend('2018-06-23','Snow',9,15)]
    (ROOT/'outputs/recommendations.json').write_text(json.dumps(examples,indent=2))
    return examples
