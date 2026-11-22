"""Pandas/NumPy features; keep target-derived columns out of model predictors."""
import logging
import numpy as np
import pandas as pd
from cleaning import RISK_WEATHER, WEATHER_ORDER
logger = logging.getLogger(__name__)

def engineer_features(cleaned, fit_end='2016-12-31 23:59:59'):
    logger.info('Before feature engineering: %d rows x %d columns', *cleaned.shape)
    df = cleaned.copy()
    dt = df.date_time.dt
    df['hour'] = dt.hour
    df['day_of_week'] = dt.dayofweek  # Monday=0
    df['is_weekend'] = df.day_of_week.ge(5).astype(int)
    df['month'] = dt.month
    df['year'] = dt.year
    df['date'] = dt.strftime('%Y-%m-%d')
    df['is_holiday'] = df.holiday.ne('None').astype(int)
    df['temp_c'] = df.temp - 273.15
    for name, period in [('hour', 24), ('day_of_week', 7), ('month', 12)]:
        offset = 1 if name == 'month' else 0
        df[f'{name}_sin'] = np.sin(2*np.pi*(df[name]-offset)/period)
        df[f'{name}_cos'] = np.cos(2*np.pi*(df[name]-offset)/period)
    df['is_low_visibility'] = df.weather_main.isin(['Fog', 'Mist', 'Haze', 'Smoke']).astype(int)
    df['is_severe_weather'] = df.weather_main.isin(['Thunderstorm', 'Snow', 'Squall']).astype(int)
    df['is_risky_weather'] = df.weather_main.isin(RISK_WEATHER).astype(int)
    # Fixed vocabulary avoids changing column order across data partitions/runs.
    for weather in WEATHER_ORDER + ['Unknown']:
        df[f'weather_{weather.lower()}'] = df.weather_main.eq(weather).astype(int)
    reference = df.loc[df.date_time <= pd.Timestamp(fit_end)]
    if reference.empty:
        raise ValueError('No observations before fit-end for fitting scaling parameters')
    scaling = {}
    for col in ['temp_c', 'rain_1h']:
        mean = float(reference[col].mean())
        std = float(reference[col].std(ddof=0))
        if not np.isfinite(std) or std == 0:
            raise ValueError(f'Cannot standardise {col}: zero or nonfinite fitting SD')
        df[f'{col}_scaled'] = (df[col]-mean)/std
        scaling[col] = {'mean': mean, 'population_sd': std}
        logger.debug('Scaling %s mean=%.6f sd=%.6f', col, mean, std)
    # Full-hourly descriptive quartiles reproduce the instructor's label definition.
    q1, q2, q3 = df.traffic_volume.quantile([.25,.5,.75]).tolist()
    logger.debug('Congestion quartiles q1=%.4f q2=%.4f q3=%.4f', q1,q2,q3)
    df['congestion_category'] = np.select([df.traffic_volume.le(q1), df.traffic_volume.le(q2),
                                            df.traffic_volume.le(q3)], ['Low','Medium','High'], default='Severe')
    df['traffic_category_part1'] = np.select([df.traffic_volume.lt(4500),df.traffic_volume.le(5500)],
                                            ['Low','Medium'], default='High')
    df['congested_part1'] = df.traffic_volume.gt(5500).astype(int)
    df['high_risk'] = (df.traffic_volume.gt(q2) & df.is_risky_weather.eq(1)).astype(int)
    excluded = ['traffic_volume','congestion_category','traffic_category_part1','congested_part1','high_risk']
    predictors = ['hour','day_of_week','is_weekend','is_holiday','hour_sin','hour_cos',
                  'day_of_week_sin','day_of_week_cos','month_sin','month_cos','temp_c_scaled',
                  'rain_1h_scaled','snow_1h','clouds_all','is_low_visibility','is_severe_weather']
    predictors += [f'weather_{w.lower()}' for w in WEATHER_ORDER+['Unknown']]
    metadata = {'fit_end': fit_end, 'scaling': scaling, 'quartiles': {'q1':q1,'q2':q2,'q3':q3},
                'quartile_scope':'all observed cleaned hourly rows; descriptive assignment labels',
                'high_risk_rule':f'traffic_volume > {q2} AND selected weather in {sorted(RISK_WEATHER)}',
                'model_predictor_columns':predictors, 'exclude_from_predictors':excluded,
                'part3_note':'For strict future evaluation refit all preprocessing and label quartiles on training data only. '
                'Do not feed contemporaneous traffic or its derived categories into the proxy classifier. '
                'The proxy is not an actual accident outcome.'}
    logger.info('High-risk label: %d of %d hours (%.4f%%)',df.high_risk.sum(),len(df),100*df.high_risk.mean())
    logger.info('After feature engineering: %d rows x %d columns', *df.shape)
    return df, metadata
