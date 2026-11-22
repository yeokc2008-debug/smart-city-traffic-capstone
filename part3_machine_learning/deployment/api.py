"""FastAPI model-serving mock. Run python -m uvicorn api:app --port 8000."""
import logging,json
from datetime import datetime
from functools import lru_cache
from typing import Literal
import pandas as pd
import joblib
from fastapi import FastAPI
from pydantic import BaseModel,Field,ConfigDict,field_validator
from config import ROOT
from data_features import build_features
logger=logging.getLogger(__name__)
app=FastAPI(title='Traffic Intelligence Teaching Mock',description='Predictions of volume and an assignment proxy; no real accident model.')

class TrafficInput(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    date_time:datetime
    weather_main:Literal['Clear','Clouds','Rain','Drizzle','Thunderstorm','Snow','Squall','Fog','Mist','Haze','Smoke']
    temp:float=Field(ge=150,le=350,description='Kelvin')
    rain_1h:float=Field(default=0,ge=0,le=9000)
    snow_1h:float=Field(default=0,ge=0,le=9000)
    clouds_all:float=Field(default=0,ge=0,le=100)
    is_holiday:bool=False
    @field_validator('date_time')
    @classmethod
    def exact_naive_hour(cls,value):
        if value.tzinfo is not None or value.minute or value.second or value.microsecond:
            raise ValueError('Use an exact source-local hour without a timezone offset')
        return value

@lru_cache(maxsize=1)
def load_bundle():
    selection=json.loads((ROOT/'models/selection.json').read_text())
    models={task:joblib.load(ROOT/'models'/f'{selection[task]}.joblib') for task in ['regression','classification']}
    logger.info('Serving mock loaded selected model versions %s %s',selection['regression'],selection['classification'])
    return selection,models

@app.get('/health')
def health():return {'status':'ready','mode':'teaching deployment simulation','actual_accident_model':False}

@app.post('/predict')
def predict(data:TrafficInput):
    selection,models=load_bundle()
    row=data.model_dump();row['holiday']='ProvidedHoliday' if row.pop('is_holiday') else 'None'
    x=build_features(pd.DataFrame([row]))[selection['feature_columns']]
    volume=float(models['regression'].predict(x)[0]);score=float(models['classification'].predict_proba(x)[0,1])
    logger.info('Prediction served timestamp=%s weather=%s',data.date_time,data.weather_main)
    return {'predicted_vehicles_per_hour':max(0,volume),'proxy_positive_score_uncalibrated':score,
            'proxy_label_at_validation_threshold':int(score>=selection['threshold']),
            'threshold':selection['threshold'],'regression_version':selection['regression'],
            'classification_version':selection['classification'],'actual_accident_prediction':False,
            'limitations':'Observed-condition volume estimate and deterministic assignment proxy; not a safety or travel-time guarantee.'}

def simulate_api():
    from fastapi.testclient import TestClient
    example={'date_time':'2018-06-18T08:00:00','weather_main':'Clear','temp':288.15,'rain_1h':0,'snow_1h':0,'clouds_all':20,'is_holiday':False}
    with TestClient(app) as client:
        valid=client.post('/predict',json=example)
        invalid=client.post('/predict',json={**example,'date_time':'bad date'})
        target=client.post('/predict',json={**example,'traffic_volume':5000})
        assert valid.status_code==200 and invalid.status_code==422 and target.status_code==422
        logger.warning('API validation simulation rejected malformed date and forbidden target input with HTTP 422')
        evidence={'method':'FastAPI TestClient in-process; network listener not required or tested',
                  'request':example,'response':valid.json(),'status_code':valid.status_code,
                  'invalid_date_status':invalid.status_code,'forbidden_target_status':target.status_code}
    (ROOT/'outputs/api_simulation.json').write_text(json.dumps(evidence,indent=2))
    return evidence
