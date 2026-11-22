"""Small command-line traffic explorer. Run python app.py --help."""
import argparse
import logging
from pathlib import Path
import sys
import pandas as pd
from logging_utils import configure_logging
logger=logging.getLogger(__name__)

def main(argv=None):
    p=argparse.ArgumentParser(description='Query observed traffic hours; no route or live travel-time predictions')
    p.add_argument('--data',default='data/processed/traffic_features.csv')
    p.add_argument('--log',default='app.log')
    p.add_argument('--debug',action='store_true')
    sub=p.add_subparsers(dest='command')
    at=sub.add_parser('at',help='Find an exact recorded local hour')
    at.add_argument('timestamp',help='YYYY-MM-DD HH:00:00')
    high=sub.add_parser('high',help='List observed hours above a traffic threshold')
    high.add_argument('--threshold',default='5500');high.add_argument('--limit',default='10')
    sub.add_parser('compare',help='Compare observed weekday and weekend traffic')
    travel=sub.add_parser('travel',help='Rank historically quieter hours inside your permitted window')
    travel.add_argument('--day-type',default='weekday')
    travel.add_argument('--start',default='7');travel.add_argument('--end',default='10')
    args=p.parse_args(argv)
    try:
        configure_logging(args.log,args.debug)
        logger.info('CLI command=%s arguments=%s',args.command,vars(args))
        if args.command is None:
            raise ValueError('Supply a command: at, high, compare or travel')
        df=pd.read_csv(Path(args.data),keep_default_na=False,parse_dates=['date_time'])
        if args.command=='at':
            stamp=pd.to_datetime(args.timestamp,format='%Y-%m-%d %H:%M:%S',errors='raise')
            if stamp!=stamp.floor('h'):
                raise ValueError('Timestamp must identify an exact hour, with minutes and seconds zero')
            rows=df.loc[df.date_time.eq(stamp),['date_time','traffic_volume','weather_main','temp_c','congestion_category','high_risk']]
            print('No observation for that hour; missing records are not zero traffic.' if rows.empty else rows.to_string(index=False))
        elif args.command=='high':
            threshold=float(args.threshold);limit=int(args.limit)
            if not 1<=limit<=100 or threshold<0 or not pd.notna(threshold) or threshold==float('inf'):
                raise ValueError('Use a finite nonnegative threshold and a limit from 1 to 100')
            rows=df.loc[df.traffic_volume.gt(threshold)].sort_values(['traffic_volume','date_time'],ascending=[False,True])
            print(f'{len(rows):,} observed hours exceed {threshold:g} vehicles/hour.')
            print(rows[['date_time','traffic_volume','weather_main']].head(limit).to_string(index=False))
        elif args.command=='compare':
            table=df.groupby('is_weekend').traffic_volume.agg(['mean','count']).rename(index={0:'Weekday',1:'Weekend'})
            print(table.to_string(float_format=lambda x:f'{x:,.2f}'))
        elif args.command=='travel':
            start=int(args.start);end=int(args.end)
            if args.day_type not in ['weekday','weekend'] or not 0<=start<=end<=23:
                raise ValueError('Use day-type weekday/weekend and 0 <= start <= end <= 23')
            rows=df.loc[df.is_weekend.eq(int(args.day_type=='weekend')) & df.hour.between(start,end)]
            if rows.empty:
                raise ValueError('No observed hours in this selection')
            table=rows.groupby('hour').traffic_volume.agg(['mean','count']).sort_values('mean')
            print(table.to_string(float_format=lambda x:f'{x:,.2f}'))
            print('Historical average volumes only. Lower volume does not guarantee shorter or safer journeys.')
        return 0
    except (ValueError,OSError,KeyError,TypeError,pd.errors.ParserError) as exc:
        if logging.getLogger().handlers:
            logger.error('Cannot answer command: %s',exc)
        else:
            sys.stderr.write(f'ERROR: Cannot configure application logging: {exc}\n')
        return 2

if __name__=='__main__':
    sys.exit(main())
