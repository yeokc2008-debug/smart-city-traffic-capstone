"""Validate first, clean transparently, then select one weather record per hour."""
import logging
import numpy as np
import pandas as pd
logger = logging.getLogger(__name__)
EXPECTED = ['holiday', 'temp', 'rain_1h', 'snow_1h', 'clouds_all',
            'weather_main', 'weather_description', 'date_time', 'traffic_volume']
# Assignment convention, not a scientifically validated hazard scale.
WEATHER_ORDER = ['Squall', 'Thunderstorm', 'Snow', 'Rain', 'Drizzle',
                 'Fog', 'Mist', 'Haze', 'Smoke', 'Clouds', 'Clear']
RISK_WEATHER = {'Squall', 'Thunderstorm', 'Snow', 'Fog', 'Mist', 'Haze', 'Smoke'}

def validate_schema(df):
    missing = sorted(set(EXPECTED) - set(df.columns))
    if missing:
        raise ValueError(f'Missing expected columns: {missing}')
    logger.info('Schema validated: all %d expected columns present', len(EXPECTED))
    extra = sorted(set(df.columns) - set(EXPECTED))
    if extra:
        logger.warning('All %d rows: ignoring extra columns %s', len(df), extra)

def warn_change(mask, reason):
    count = int(mask.sum())
    if count:
        logger.warning('%d rows affected: %s', count, reason)
    else:
        logger.info('0 rows affected: %s', reason)

def clean_data(raw, collapse='severe', fit_end='2016-12-31 23:59:59'):
    validate_schema(raw)  # No processing before this guard.
    df = raw[EXPECTED].copy()
    audit = {'raw_rows': len(df), 'raw_columns': len(raw.columns), 'collapse_rule': collapse, 'weather_order': WEATHER_ORDER}
    for col in ['holiday', 'weather_main', 'weather_description']:
        old = df[col].astype(str)
        new = old.str.strip().str.replace(r'\s+', ' ', regex=True)
        if col == 'weather_main':
            mapping = {x.casefold(): x for x in WEATHER_ORDER}
            new = new.str.casefold().map(mapping).fillna('Unknown')
        elif col == 'holiday':
            canonical = ['None', 'Columbus Day', 'Veterans Day', 'Thanksgiving Day', 'Christmas Day',
                         'New Years Day', 'Washingtons Birthday', 'Memorial Day', 'Independence Day',
                         'State Fair', 'Labor Day', 'Martin Luther King Jr Day']
            mapping = {v.casefold(): v for v in canonical}
            new = new.str.casefold().map(mapping).fillna(new)
            new = new.mask(new.str.casefold().isin(['', 'none', 'nan', 'null']), 'None')
        else:
            new = new.str.lower().replace({'': 'unknown'})
        warn_change(new.ne(old), f'standardise {col}')
        df[col] = new
    parsed = pd.to_datetime(df.date_time, format='%Y-%m-%d %H:%M:%S', errors='coerce')
    bad = parsed.isna() | parsed.ne(parsed.dt.floor('h'))
    warn_change(bad, 'drop invalid or non-hourly timestamps')
    df['date_time'] = parsed
    df = df.loc[~bad].copy()
    audit['invalid_datetime_dropped'] = int(bad.sum())
    dup = df.duplicated()
    audit['exact_duplicates_dropped'] = int(dup.sum())
    warn_change(dup, 'remove exact duplicate rows')
    df = df.loc[~dup].copy()
    df['_source_order'] = np.arange(len(df))
    for col in ['temp', 'rain_1h', 'snow_1h', 'clouds_all', 'traffic_volume']:
        before = df[col]
        numeric = pd.to_numeric(before, errors='coerce')
        warn_change(numeric.isna() & before.notna(), f'coerce nonnumeric {col} to missing')
        df[col] = numeric
    bad_target = (~np.isfinite(df.traffic_volume) | (df.traffic_volume < 0)
                  | (df.traffic_volume.mod(1) != 0))
    warn_change(bad_target, 'drop missing, negative or fractional traffic targets; do not impute target')
    df = df.loc[~bad_target].copy()
    df['traffic_volume'] = df.traffic_volume.astype(int)
    # Explicit broad validation ranges; rain >9000 matches the assignment anomaly.
    ranges = {'temp': (150, 350), 'rain_1h': (0, 9000), 'snow_1h': (0, 9000), 'clouds_all': (0, 100)}
    stats = {}
    for col, (lo, hi) in ranges.items():
        bad = ~np.isfinite(df[col]) | ~df[col].between(lo, hi)
        audit[f'{col}_imputed'] = int(bad.sum())
        warn_change(bad, f'{col} outside [{lo}, {hi}] or missing; mark for monthly median imputation')
        df.loc[bad, col] = np.nan
        # One contribution per timestamp for fitting avoids overweighting overlapping weather rows.
        reference = df.loc[df.date_time <= pd.Timestamp(fit_end)].drop_duplicates('date_time')
        fallback = reference[col].median()
        if pd.isna(fallback):
            raise ValueError(f'No valid fitting values for {col} through {fit_end}')
        stats[col] = {'fallback': float(fallback), 'monthly': {}}
        for month in range(1, 13):  # Explicit group-by-group imputation.
            median = reference.loc[reference.date_time.dt.month.eq(month), col].median()
            median = float(fallback if pd.isna(median) else median)
            stats[col]['monthly'][str(month)] = median
            mask = bad & df.date_time.dt.month.eq(month)
            if mask.any():
                df.loc[mask, col] = median
                logger.warning('%d rows imputed: %s month=%d median=%.4f', mask.sum(), col, month, median)
            logger.debug('Imputation %s month=%d median=%.4f', col, month, median)
    # Midnight holiday markers label their observed calendar date, not missing hours/days.
    day = df.date_time.dt.normalize()
    holidays = df.loc[df.holiday.ne('None')].groupby(day)['holiday'].agg(lambda s: sorted(set(s))[0])
    expanded = day.map(holidays).fillna('None')
    warn_change(expanded.ne(df.holiday), 'propagate holiday marker within observed calendar date')
    df['holiday'] = expanded
    conflicts = df.groupby('date_time').traffic_volume.nunique().gt(1)
    audit['timestamps_with_conflicting_volume'] = int(conflicts.sum())
    if conflicts.any():
        raise ValueError('Conflicting traffic volumes within hour; resolve explicitly before consolidation')
    audit['repeated_timestamps'] = int(df.date_time.duplicated(keep=False).groupby(df.date_time).any().sum())
    if collapse == 'severe':
        df['_rank'] = df.weather_main.map({v:i for i,v in enumerate(WEATHER_ORDER)}).fillna(99)
        df = df.sort_values(['date_time', '_rank', '_source_order'], kind='stable')
    elif collapse != 'first':
        raise ValueError('collapse must be severe or first')
    repeated = df.duplicated('date_time')
    warn_change(repeated, f'collapse repeated hours using {collapse} weather selection')
    df = df.loc[~repeated].sort_values('date_time').drop(columns=['_source_order', '_rank'], errors='ignore').reset_index(drop=True)
    if df.empty:
        raise ValueError('No valid hourly observations remain')
    audit['hourly_rows'] = len(df)
    audit['first_timestamp'] = str(df.date_time.min())
    audit['last_timestamp'] = str(df.date_time.max())
    expected_hours = len(pd.date_range(df.date_time.min(), df.date_time.max(), freq='h'))
    audit['missing_hours_within_span'] = expected_hours - len(df)
    logger.info('Hourly cleaning complete: %d rows, %d missing hours within span retained as gaps', len(df), audit['missing_hours_within_span'])
    return df, audit, stats
