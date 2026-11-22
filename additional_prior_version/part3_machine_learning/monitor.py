import json,logging,pandas as pd
from pathlib import Path
logging.basicConfig(level=logging.INFO); logger=logging.getLogger(__name__); ROOT=Path(__file__).resolve().parents[1]; df=pd.read_csv(ROOT/'data/processed/traffic_clean.csv',parse_dates=['date_time']); split=df.date_time.quantile(.8); base=df[df.date_time<=split]; recent=df[df.date_time>split]; alerts=[]
for c in ['temp','clouds_all','traffic_volume']:
 shift=abs(recent[c].mean()-base[c].mean())/(base[c].std() or 1)
 if shift>.5: alerts.append(f'{c} mean shifted by {shift:.2f} baseline SD')
status='ALERT / Requires investigation' if alerts else 'PASS / Normal'; (Path(__file__).parent/'monitoring_status.json').write_text(json.dumps({'status':status,'alerts':alerts},indent=2)); (logger.warning if alerts else logger.info)('%s: %s',status,alerts)
