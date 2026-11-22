"""Build a native PBIP/PBIR source project with an embedded hourly import model."""
import json,base64,zlib,logging,sys,hashlib
from pathlib import Path
import pandas as pd
logger=logging.getLogger(__name__)
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'PowerBI';REPORT=OUT/'Traffic.Report';MODEL=OUT/'Traffic.SemanticModel'
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,indent=2))
def schema(kind,version):return f'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/{kind}/{version}/schema.json'
def field(name,measure=False):return {('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':'TrafficHourly'}},'Property':name}}
def proj(name,measure=False):return {'field':field(name,measure),'queryRef':'TrafficHourly.'+name,'nativeQueryRef':name}
def visual(name,typ,x,y,w,h,roles,title,year=None):
    v={'$schema':schema('visualContainer','2.1.0'),'name':hashlib.md5(name.encode()).hexdigest()[:20],'position':{'x':x,'y':y,'width':w,'height':h,'z':0,'tabOrder':0},'visual':{'visualType':typ,'query':{'queryState':{role:{'projections':[proj(c,m) for c,m in pairs]} for role,pairs in roles.items()}},'visualContainerObjects':{'title':[{'properties':{'show':{'expr':{'Literal':{'Value':'true'}}},'text':{'expr':{'Literal':{'Value':"'"+title+"'"}}}}}]},'drillFilterOtherVisuals':True}}
    if year:
        f=field('Year');v['filterConfig']={'filters':[{'name':name+'_year','field':f,'type':'Categorical','filter':{'Version':2,'From':[{'Name':'t','Entity':'TrafficHourly','Type':0}],'Where':[{'Condition':{'In':{'Expressions':[{'Column':{'Expression':{'SourceRef':{'Source':'t'}},'Property':'Year'}}],'Values':[[{'Literal':{'Value':str(k)+'L'}}] for k in year]}}}]}}]}
    return v
def run():
    d=pd.read_csv(ROOT/'data/traffic_clean.csv',keep_default_na=False)
    # Embed data so project is portable and does not need machine-specific file paths.
    raw=ROOT/'data/Metro_Interstate_Traffic_Volume.csv'
    raw_payload=base64.b64encode(zlib.compress(raw.read_bytes())[2:-4]).decode()
    raw_m=(OUT/'TrafficRaw.m').read_text().replace('File.Contents(CsvPath)','Binary.Decompress(Binary.FromText("'+raw_payload+'",BinaryEncoding.Base64),Compression.Deflate)')
    raw_m='\n'.join(line for line in raw_m.splitlines() if not line.strip().startswith('//'))
    hourly_m=(OUT/'TrafficHourly.m').read_text()
    cols={c:'string' for c in d.columns};cols.update({c:'double' for c in ['temp','rain_1h','snow_1h']});cols.update({'date_time':'dateTime','traffic_volume':'int64','clouds_all':'int64','Hour':'int64','Date':'dateTime','Year':'int64','Temperature Celsius':'double','Traffic Category':'string'})
    measures=[]
    for line in (OUT/'Measures.dax').read_text().splitlines():
        if line.strip() and not line.startswith('//'):
            n,e=line.split('=',1);name=n.strip();fmt='0.00%' if 'Probability' in name or 'Given' in name else '#,0.00';measures.append({'name':name,'expression':e.strip(),'formatString':fmt})
    def table(name,columns,expression,ms=None):
        return {'name':name,'columns':[{'name':c,'dataType':typ,'sourceColumn':c,'summarizeBy':'none'} for c,typ in columns.items()],'measures':ms or [],'partitions':[{'name':name+'Import','mode':'import','source':{'type':'m','expression':expression.splitlines()}}]}
    rawcols={c:cols[c] for c in d.columns}
    tables=[table('TrafficRaw',rawcols,raw_m),table('TrafficHourly',cols,hourly_m,measures)]
    quality_m='let R=TrafficRaw in #table(type table [Check=text,Value=text],{{"Original rows",Text.From(Table.RowCount(R))},{"Original columns",Text.From(Table.ColumnCount(R))},{"Exact duplicate rows",Text.From(Table.RowCount(R)-Table.RowCount(Table.Distinct(R)))},{"Zero Kelvin records",Text.From(Table.RowCount(Table.SelectRows(R,each [temp]=0)))},{"Rain above 9000 mm",Text.From(Table.RowCount(Table.SelectRows(R,each [rain_1h]>9000)))},{"Unique observed hours",Text.From(List.Count(List.Distinct(R[date_time])))}})'
    tables.append(table('DataQuality',{'Check':'string','Value':'string'},quality_m))
    write(MODEL/'definition.pbism',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{}})
    write(MODEL/'model.bim',{'name':'Traffic','compatibilityLevel':1567,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','tables':tables,'annotations':[{'name':'SourceGrain','value':'40,575 unique observed hours; source pipeline training-only weather repairs'}]}})
    write(REPORT/'definition.pbir',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../Traffic.SemanticModel'}}})
    write(OUT/'Traffic_Intelligence.pbip',{'version':'1.0','artifacts':[{'report':{'path':'Traffic.Report'}}],'settings':{'enableAutoRecovery':True}})
    write(REPORT/'definition/version.json',{'$schema':schema('versionMetadata','1.0.0'),'version':'2.0.0'})
    write(REPORT/'definition/report.json',{'$schema':schema('report','3.0.0'),'themeCollection':{},'settings':{'useStylableVisualContainerHeader':True}})
    page=hashlib.md5(b'Traffic Intelligence').hexdigest()[:20];base=REPORT/'definition/pages'/page
    write(REPORT/'definition/pages/pages.json',{'$schema':schema('pagesMetadata','1.0.0'),'pageOrder':[page],'activePageName':page})
    write(base/'page.json',{'$schema':schema('page','2.0.0'),'name':page,'displayName':'Traffic Intelligence','displayOption':'FitToPage','height':900,'width':1440})
    defs=[visual('hours','card',20,10,300,110,{'Values':[('Total Hours Analysed',True)]},'Total observed hours'),visual('avg','card',360,10,300,110,{'Values':[('Average Traffic Volume',True)]},'Average vehicles per hour'),visual('temperature','card',700,10,300,110,{'Values':[('Average Temperature Celsius',True)]},'Average temperature Celsius'),visual('hour_filter','slicer',20,130,400,110,{'Values':[('Hour',False)]},'Hour range'),visual('weather_filter','slicer',460,130,440,110,{'Values':[('weather_main',False)]},'Weather'),visual('category_filter','slicer',940,130,480,110,{'Values':[('Traffic Category',False)]},'Traffic category'),visual('daily','lineChart',20,260,690,290,{'Category':[('Date',False)],'Y':[('Average Traffic Volume',True)]},'Daily average traffic 2015 to 2017',[2015,2016,2017]),visual('hourly','clusteredColumnChart',730,260,690,290,{'Category':[('Hour',False)],'Y':[('Average Traffic Volume',True)]},'Hourly traffic 2017',[2017]),visual('weather','clusteredBarChart',20,570,690,290,{'Category':[('weather_main',False)],'Y':[('Average Traffic Volume',True)]},'Weather and traffic'),visual('scatter','scatterChart',730,570,690,290,{'Category':[('date_time',False)],'X':[('Temperature Celsius',False)],'Y':[('traffic_volume',False)]},'Temperature and traffic')]
    for v in defs:write(base/'visuals'/v['name']/'visual.json',v)
    page2=hashlib.md5(b'Annual and Data Quality').hexdigest()[:20];b2=REPORT/'definition/pages'/page2
    write(REPORT/'definition/pages/pages.json',{'$schema':schema('pagesMetadata','1.0.0'),'pageOrder':[page,page2],'activePageName':page})
    write(b2/'page.json',{'$schema':schema('page','2.0.0'),'name':page2,'displayName':'Annual and Data Quality','displayOption':'FitToPage','height':900,'width':1440})
    summary=visual('annual_table','tableEx',20,20,900,350,{'Values':[('Year',False),('Total Hours Analysed',True),('Total Observed Volume',True),('Average Traffic Volume',True)]},'Yearly observed traffic',[2012,2013,2014,2015,2016,2017])
    weather_table=visual('weather_table','tableEx',20,400,900,450,{'Values':[('weather_main',False),('Total Hours Analysed',True),('Average Traffic Volume',True)]},'Weather averages with sample sizes')
    quality=visual('quality_table','tableEx',950,20,470,480,{'Values':[('Check',False),('Value',False)]},'Source quality checks')
    for role in quality['visual']['query']['queryState'].values():
        for pr in role['projections']:
            pr['field']['Column']['Expression']['SourceRef']['Entity']='DataQuality';pr['queryRef']=pr['queryRef'].replace('TrafficHourly.','DataQuality.')
    for v in [summary,weather_table,quality]:write(b2/'visuals'/v['name']/'visual.json',v)
    # Native between slicer mode.
    p=base/'visuals'/hashlib.md5(b'hour_filter').hexdigest()[:20]/'visual.json';v=json.loads(p.read_text());v['visual']['objects']={'data':[{'properties':{'mode':{'expr':{'Literal':{'Value':"'Between'"}}}}}]};write(p,v)
    (OUT/'GENERATED_PROJECT_NOTES.md').write_text('''# Native Power BI source project

Open Traffic_Intelligence.pbip in Power BI Desktop (standard edition), then Refresh. The original CSV is embedded and the TrafficHourly M query cleans and consolidates it; no local CSV path is needed. The project defines three KPI cards, three slicers and four charts. Daily and hourly charts have the specified year filters.

This PBIP/PBIR project was generated and JSON-schema checked externally. Power BI Desktop loading and runtime rendering have not been verified here. Check slicer interactions and data import in Desktop, save as Traffic_Intelligence.pbix and capture screenshots there. Do not rename a PBIP or ZIP to PBIX. The HTML screenshots supplied separately are labelled browser companion images, not Power BI screenshots.

Regenerate after changing the data with python tools/build_powerbi.py. The M queries import the embedded original CSV, repair weather readings, remove exact duplicates, consolidate hours, expand holiday labels and create Hour, Date, Year, Celsius and the fixed traffic category.
''')
    logger.info('Native Power BI project generated at %s',OUT)
if __name__=='__main__':run()
