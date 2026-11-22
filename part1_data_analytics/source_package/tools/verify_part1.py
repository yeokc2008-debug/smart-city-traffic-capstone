import logging,sqlite3,json,math,re,base64,zlib,io
from pathlib import Path
import pandas as pd
logger=logging.getLogger(__name__)
ROOT=Path(__file__).resolve().parents[1]
def run():
 d=pd.read_csv(ROOT/'data/traffic_clean.csv',keep_default_na=False);ready=pd.read_csv(ROOT/'data/Traffic_PowerBI_Ready.csv',keep_default_na=False)
 assert len(d)==40575 and d.date_time.is_unique and ready.shape==(40575,14)
 assert set(ready['Traffic Category'])=={'Low','Medium','High'}
 assert all(ready.loc[ready.traffic_volume.eq(4500),'Traffic Category'].eq('Medium'))
 assert all(ready.loc[ready.traffic_volume.eq(5500),'Traffic Category'].eq('Medium'))
 stats=pd.read_csv(ROOT/'results/traffic_statistics.csv').iloc[0];prob=pd.read_csv(ROOT/'results/probability_analysis.csv').iloc[0]
 assert math.isclose(stats.mean_traffic,d.traffic_volume.mean())
 assert math.isclose(stats.sample_variance,d.traffic_volume.var())
 assert math.isclose(prob.p_congestion,(d.traffic_volume>5500).mean())
 with sqlite3.connect(ROOT/'sql/traffic.sqlite') as c:
  assert c.execute('SELECT COUNT(*) FROM traffic_raw').fetchone()[0]==48204
  assert c.execute('SELECT COUNT(*) FROM traffic_hourly').fetchone()[0]==40575
  assert c.execute('SELECT SUM(traffic_volume>5500) FROM traffic_hourly').fetchone()[0]==6107
 model=json.loads((ROOT/'PowerBI/Traffic.SemanticModel/model.bim').read_text());tables={t['name']:t for t in model['model']['tables']}
 expression='\n'.join(tables['TrafficRaw']['partitions'][0]['source']['expression']);payload=re.search(r'Binary.FromText\("([^"]+)"',expression).group(1)
 embedded=pd.read_csv(io.BytesIO(zlib.decompress(base64.b64decode(payload),-15)),keep_default_na=False)
 original=pd.read_csv(ROOT/'data/Metro_Interstate_Traffic_Volume.csv',keep_default_na=False);pd.testing.assert_frame_equal(embedded,original)
 definitions=ROOT/'PowerBI/Traffic.Report/definition';assert json.loads((definitions/'version.json').read_text())['version']=='2.0.0'
 assert len(json.loads((definitions/'pages/pages.json').read_text())['pageOrder'])==2
 visuals=list(definitions.rglob('visual.json'));assert len(visuals)==13
 for path in visuals:
  v=json.loads(path.read_text())
  for role in v['visual']['query']['queryState'].values():
   for pr in role['projections']:
    f=next(iter(pr['field'].values()));entity=f['Expression']['SourceRef']['Entity'];names={c['name'] for c in tables[entity]['columns']}|{m['name'] for m in tables[entity].get('measures',[])};assert f['Property'] in names
 validation=json.loads((ROOT/'PowerBI/schema_validation.json').read_text());assert len(validation)==20 and not any(v['errors'] for v in validation)
 status={'source_rows':48204,'hourly_rows':40575,'prepared_columns':14,'congested_hours':6107,'SQL_Python_results':'PASS','embedded_source_matches_original':'PASS','PowerBI_pages':2,'PowerBI_visuals':13,'schema_documents':20,'PowerBI_Desktop_runtime':'NOT_VERIFIED'}
 (ROOT/'results/verification_checks.json').write_text(json.dumps(status,indent=2));logger.info('Part 1 verification passed %s',status)
if __name__=='__main__':
 logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(name)s %(message)s');run()
