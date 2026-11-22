"""Save numerical support for report findings and visual interpretations."""
import json
import logging
from pathlib import Path
logger=logging.getLogger(__name__)

def write_summaries(df, output_dir):
    out=Path(output_dir)
    for name,table in [
        ('hourly_by_day_type.csv',df.groupby(['is_weekend','hour']).traffic_volume.agg(['mean','count'])),
        ('weather_summary.csv',df.groupby('weather_main').traffic_volume.agg(['mean','count'])),
        ('yearly_summary.csv',df.groupby('year').traffic_volume.agg(['sum','mean','count'])),
        ('monthly_coverage.csv',df.groupby(df.date_time.dt.to_period('M')).traffic_volume.agg(['mean','count']))]:
        table.to_csv(out/name)
        logger.info('Saved summary: %s',out/name)
    result={'hours':len(df),'mean_traffic':float(df.traffic_volume.mean()),'median_traffic':float(df.traffic_volume.median()),
            'sd_traffic':float(df.traffic_volume.std()),'mean_temp_c':float(df.temp_c.mean()),
            'temperature_correlation':float(df.temp_c.corr(df.traffic_volume)),
            'high_risk_hours':int(df.high_risk.sum()),'high_risk_percent':float(100*df.high_risk.mean()),
            'part1_congested_hours':int(df.congested_part1.sum()),
            'weekday_mean':float(df.loc[df.is_weekend.eq(0)].traffic_volume.mean()),
            'weekend_mean':float(df.loc[df.is_weekend.eq(1)].traffic_volume.mean())}
    (out/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    logger.info('Saved summary: %s',out/'summary.json')
