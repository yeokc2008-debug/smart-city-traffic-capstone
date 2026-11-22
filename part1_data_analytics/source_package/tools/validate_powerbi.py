import json,requests,logging
from pathlib import Path
from urllib.parse import urljoin
from jsonschema import Draft7Validator,RefResolver
logger=logging.getLogger(__name__)
root=Path(__file__).resolve().parents[1]/'PowerBI';cache={}
def retrieve(uri):
 if uri not in cache:
  r=requests.get(uri.replace("schema.embedded.json","schema-embedded.json"),timeout=15);r.raise_for_status();cache[uri]=r.json()
 return cache[uri]
results=[]
for p in root.rglob('*'):
 if p.suffix not in ['.json','.pbir','.pbism']:continue
 d=json.loads(p.read_text());uri=d.get('$schema')
 if not uri:continue
 try:
  s=retrieve(uri);res=RefResolver(uri,s,handlers={'https':retrieve});errors=list(Draft7Validator(s,resolver=res).iter_errors(d))
  results.append({'file':str(p.relative_to(root)),'errors':[str(e.message) for e in errors]})
 except Exception as e:results.append({'file':str(p.relative_to(root)),'errors':[str(e)]})
(root/'schema_validation.json').write_text(json.dumps(results,indent=2))
logger.info('Validated %s report/property documents; errors=%s',len(results),[r for r in results if r['errors']])
