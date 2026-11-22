import logging,json
from pathlib import Path
import pandas as pd
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
logger=logging.getLogger(__name__)
R=Path(__file__).resolve().parents[1]
def new(title):
 d=Document();s=d.sections[0];s.page_width=Inches(8.5);s.page_height=Inches(11);s.top_margin=s.bottom_margin=Inches(.65);s.left_margin=s.right_margin=Inches(.7)
 for name in ['Normal','Title','Heading 1','Heading 2']:
  st=d.styles[name];st.font.name='Calibri';st.font.color.rgb=RGBColor(0,0,0)
 d.styles['Normal'].font.size=Pt(10);d.styles['Normal'].paragraph_format.space_after=Pt(4);d.styles['Title'].font.size=Pt(23);d.styles['Heading 1'].font.size=Pt(14)
 for node in list(d.styles.element.iter(qn('w:pBdr'))):node.getparent().remove(node)
 d.add_paragraph(title,'Title');return d
def p(d,t):d.add_paragraph(t)
def h(d,t):d.add_paragraph(t,'Heading 1')
def table(d,headers,rows):
 t=d.add_table(rows=1,cols=len(headers));t.style='Table Grid'
 for c,v in zip(t.rows[0].cells,headers):c.text=str(v)
 for row in rows:
  for c,v in zip(t.add_row().cells,row):c.text=str(v)
 for i,row in enumerate(t.rows):
  for c in row.cells:
   pr=c._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
   for edge in ['top','bottom','left','right']:
    e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');b.append(e)
   pr.append(b)
   if i==0:
    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EEF3');pr.append(sh)
    for run in c.paragraphs[0].runs:run.bold=True
 return t
def save(d,name):d.save(R/'report'/name);logger.info('Saved report %s',name)
def run():
 a=pd.read_csv(R/'results/annual_hourly.csv');raw=pd.read_csv(R/'results/annual_raw.csv');s=json.loads((R/'results/statistics.json').read_text())['hourly_clean'];holiday=pd.read_csv(R/'results/holiday_daily.csv');hw=pd.read_csv(R/'results/holiday_raw.csv');w=pd.read_csv(R/'results/weather_hourly.csv');dset=pd.read_csv(R/'data/Traffic_PowerBI_Ready.csv');temp=dset.loc[dset.traffic_volume>5500,'Temperature Celsius']
 annual=[[int(r.year),f'{int(r.observed_hours):,}',f'{r.total_observed_traffic:,.0f}',f'{r.average_traffic:.2f}','—' if pd.isna(r.change) else f'{r.change:,.0f}','—' if pd.isna(r.change_pct) else f'{r.change_pct:.2f}%'] for r in a.itertuples()]
 statrows=[['Mean',f'{s["mean"]:,.2f}'],['Median',f'{s["median"]:,.0f}'],['Sample standard deviation',f'{s["std_sample"]:,.2f}'],['Sample variance',f'{s["variance_sample"]:,.2f}'],['Range',f'{s["range"]:,.0f}'],['Temperature correlation',f'{s["pearson_temp_traffic"]:.4f}']]
 prows=[['P Congestion','6107 / 40575',f'{s["P_congestion"]:.4%}'],['P Clear','13371 / 40575',f'{s["P_clear"]:.4%}'],['P Congestion and Clear','1763 / 40575',f'{s["P_congestion_and_clear"]:.4%}'],['P Clear given Congestion','1763 / 6107',f'{s["P_clear_given_congestion"]:.4%}'],['P Temperature above 292 K given Congestion','1699 / 6107',f'{s["P_high_temp_given_congestion"]:.4%}']]
 # REQUIRED TWO PAGE INSIGHTS REPORT
 d=new('Data Analytics Insights Report')
 p(d,'Part 1 completed analysis of the supplied Metro Interstate Traffic Volume dataset. Main findings use 40,575 distinct observed hours to avoid repeated weather records weighting the traffic totals. Original-record comparisons are retained. Time schedules and data coverage matter more than the weak temperature association.')
 h(d,'Task 1 Annual traffic and holiday temperatures')
 table(d,['Year','Hours','Observed volume','Mean per hour','Change','Change percent'],annual)
 p(d,'Observed totals fall 39.03% in 2014 and 20.47% in 2015, then rise 113.84% in 2016 and 17.53% in 2017. These are changes in recorded totals, not complete annual demand: September 2014–May 2015 is absent and 2012 starts in October. Average observed traffic changes much less, from 3,310 vehicles/hour in 2013 to 3,377 in 2017. Do not size capacity from annual sums without coverage checks.')
 p(d,'Observed-day Labor Day temperatures are 295.32 K in 2015, 295.01 K in 2016 and 291.29 K in 2017 (changes −0.32 K and −3.72 K). New Year 2015 is missing; 2016 and 2017 means are 267.09 K and 271.85 K (+4.76 K), using 18 and 24 hours. An explicitly additional 2018 comparison is 250.97 K. Sparse holiday observations cannot establish a temperature effect on traffic; schedule, season and missingness remain competing explanations.')
 h(d,'Task 2 Statistics and correlation')
 table(d,['Hourly statistic','Result'],statrows)
 p(d,'Standard deviation is about 60% of the mean, showing substantial quiet/busy-hour variability. The weak positive Pearson correlation indicates little linear temperature association. Time of day, season and weekday/holiday patterns can confound both variables; correlation does not imply causation.')
 d.add_page_break();h(d,'Task 3 Probability and congestion')
 table(d,['Event','Calculation','Probability'],prows)
 p(d,'Congestion is volume >5,500. Clear means primary weather_main exactly Clear. The observed joint probability 0.043450 differs from P Congestion × P Clear = 0.049599; the empirical independence equality does not hold. This is a descriptive check, not an independent-sample significance test.')
 p(d,'Clear: 1,763 congested and 11,608 noncongested hours. Clouds: 2,585 and 12,531. Odds ratio = (1763 × 12531)/(11608 × 2585) = 0.7362. Clear-weather congestion odds are about 26.4% lower than Clouds in the observed data, before controlling for hour, season or day type. The result supports association, not a causal weather intervention.')
 h(d,'Task 4 Data preparation and dashboard findings')
 p(d,'Raw data has 48,204 rows and nine columns. There are no blank source cells; holiday None is a valid non-holiday token. Seventeen exact duplicates and overlapping weather rows are consolidated; ten 0 K temperatures and one 9,831.3 mm rainfall value are repaired with documented month medians learned through 2016. Hourly timestamps are unique. Power Query definitions perform typing, cleaning, holiday expansion, hourly consolidation, Hour/Date/Year extraction, Celsius conversion and the required traffic bands.')
 p(d,'Hourly Smoke has the highest average (4,443.00 vehicles/hour; only two observations), Squall the lowest (2,061.75; four observations); difference 2,381.25. These rare categories are unstable comparisons. The raw-record ranking is Clouds highest and Squall lowest, difference 1,556.70. Keep the grains separate.')
 p(d,f'Daily 2015–2017 charts reveal coverage gaps and day-to-day variation; 2017 hourly bars show commute/daytime peaks and overnight lows. The temperature scatter has broad vertical spread. The middle 80% of high-volume hours spans {temp.quantile(.1):.1f} to {temp.quantile(.9):.1f} °C; the full range is {temp.min():.1f} to {temp.max():.1f} °C. Raw 0 K readings are sensor anomalies and are repaired, while zero traffic is retained without independent proof of an outage.')
 p(d,f'All-data KPI checks: 40,575 observed hours; mean traffic 3,290.65; mean temperature {dset["Temperature Celsius"].mean():.2f} °C. Use hour, weather and category slicers. Prioritise time-aware staffing and travel-window trials, monitor coverage and validate weather effects before policy changes. Native Power BI source has two pages; Desktop rendering/PBIX export remains unverified. The HTML dashboard is a separately labelled working companion.')
 save(d,'Data_Analytics_Insights_Report.docx')
 # DETAILED WORKED ANSWERS
 d=new('Part 1 Worked Answers')
 p(d,'Complete worked answers and supporting evidence for Tasks 1.1–4.3. The cleaned hourly dataset is authoritative for inference about hours. Raw records are supplied to reproduce original-file totals and demonstrate sensitivity. A native Power BI project is prepared but its Desktop loading/export must still be verified on the user’s machine.')
 h(d,'Task 1 point 1 Load and verify SQLite')
 p(d,'sql/traffic.sqlite contains traffic_raw (48,204 rows), traffic_hourly_materialized (40,575 rows) and the traffic_hourly view. The source has nine columns, earliest time 2012-10-02 09:00 and latest 2018-09-30 23:00. tools/run_part1.py imports both comma-delimited files and runs all twelve SELECT statements in sql/queries.sql; the twelve outputs are in results/. SQL and Python both count 6,107 congested hours. The database already contains the loaded data, so no manual import is needed to inspect results.')
 h(d,'Task 1 point 2 Annual hourly totals and changes')
 table(d,['Year','Hours','Observed volume','Mean per hour','Change','Change percent'],annual)
 p(d,'Change = current observed total − previous observed total. Percentage change = change / previous total ×100. The first year has no previous-year comparison and returns NULL. Total observed volume is a sum of vehicles in recorded hours, not a complete-year traffic census.')
 table(d,['Year','Original records','Raw recorded total','Raw mean'],[[int(r.year),f'{r.records:,}',f'{r.total_record_volume:,}',f'{r.average_traffic:.2f}'] for r in raw.itertuples()])
 p(d,'Observation 1: 2012’s partial October–December coverage explains much of the apparent 255.74% increase in 2013. Observation 2: missing September 2014–May 2015 depresses 2014/2015 totals and inflates the 2016 recovery. Observation 3: 2017 has more observed hours than 2016 and a higher hourly mean; quantify both effects rather than attributing the entire 17.53% rise to demand.')
 d.add_page_break();h(d,'Task 1 point 3 Holiday temperatures')
 table(d,['Year','Holiday','Mean K','Mean Celsius','Observed hours'],[[r.year,r.holiday,f'{r.kelvin:.2f}',f'{r.celsius:.2f}',r.n] for r in holiday.itertuples()])
 p(d,'Holiday flags occur at midnight in the original data. The hourly preparation propagates the marker only within each observed calendar date, so these are observed-day means. Labor Day changes are −0.32 K then −3.72 K. New Year’s Day rises by 4.76 K from 2016 to 2017. New Year 2015 has no records and must not be fabricated; the supplementary file provides 2014 and 2018, with 2018 explicitly used as an additional comparison.')
 table(d,['Year','Holiday','Original flagged mean K','Celsius','Raw records'],[[r.year,r.holiday,f'{r.kelvin:.2f}',f'{r.celsius:.2f}',r.n] for r in hw.itertuples()])
 p(d,'If the task is interpreted as using original holiday-labelled records only, Labor Day changes are −1.85 K and +2.37 K, and New Year 2016–2017 changes +4.68 K. These differ from full observed-day averages because they sample midnight and sometimes repeat a weather record. Both interpretations are explicitly documented. Neither comparison alone establishes relevance to traffic: seasonal temperature, weekday effects and holiday schedules must be controlled.')
 h(d,'Task 2 point 1 Descriptive statistics')
 table(d,['Hourly statistic','Result'],statrows[:5])
 p(d,'Mean = sum(volume)/n. Median is the middle sorted value. Sample variance = sum((volume−mean)²)/(n−1); sample SD is its square root; range = maximum−minimum = 7280−0. Sample rather than population formulas are explicitly used. Variance units are squared volume units. The large SD shows a broad distribution driven by traffic schedules and conditions, so a single average does not describe every hour.')
 h(d,'Task 2 point 2 Correlation')
 p(d,f'Pearson r = sum((temperature−mean temperature)(volume−mean volume)) / sqrt(sum((temperature−mean temperature)²) × sum((volume−mean volume)²)) = {s["pearson_temp_traffic"]:.6f}. Direction is positive and strength is weak. Celsius and Kelvin give the same correlation because subtracting a constant does not change it. Correlation cannot establish causation because schedules, season and other conditions may influence both variables.')
 d.add_page_break();h(d,'Task 3 Basic and conditional probabilities')
 table(d,['Event','Calculation','Probability'],prows)
 p(d,'Let A be congestion, B be Clear and H be temperature >292 K (18.85 °C). There are n=40,575 hours, |A|=6,107, |B|=13,371, |A∩B|=1,763 and |A∩H|=1,699. P(B|A)=P(A∩B)/P(A), and similarly for H. These are empirical probabilities over the observed hours only.')
 h(d,'Task 3 Independence and odds ratio')
 p(d,'P(A∩B)=0.043450, whereas P(A)P(B)=0.150511×0.329538=0.049599. Since they are unequal, empirical independence is not supported by the requested equality check. Temporal dependence, sampling gaps and weather prioritisation limit inferential conclusions. Formal significance is not claimed.')
 table(d,['Weather','Congested','Not congested'],[['Clear',1763,11608],['Clouds',2585,12531]])
 p(d,'Odds Clear = 1763/11608 ≈0.1519; odds Clouds = 2585/12531 ≈0.2063. OR = 0.736241, meaning lower observed congestion odds under Clear relative to Clouds. This is an odds comparison, not a 26.4 percentage-point reduction in congestion probability. Weather and congestion are associated in these data, but hour/season/day-type confounding prevents causal attribution.')
 h(d,'Task 4 point 1 Quality typing and transformations')
 table(d,['Check','Answer'],[['Raw shape','48,204 rows ×9 columns'],['Blank or null source cells','0; literal holiday None is a valid category'],['Exact duplicate rows','17'],['Repeated-hour issue','5,445 timestamps have more than one raw row; retain one primary weather per observed hour'],['Impossible weather','10 zero-K records; 1 rainfall reading of 9,831.3 mm'],['Prepared hourly shape','40,575 rows ×14 columns including five derived fields']])
 p(d,'Types: date_time Date/Time; traffic_volume and clouds_all whole numbers; temp/rain/snow decimal numbers; holiday/weather text. Derived fields: Hour=Time.Hour(DateTime.Time(date_time)); Date=Date.From(date_time); Year=Date.Year(Date); Celsius=temp−273.15. Category: volume<4500 Low, volume≤5500 Medium, otherwise High. Both 4,500 and 5,500 belong to Medium. Power Query code is in PowerBI/TrafficRaw.m and TrafficHourly.m and is embedded in the native model. Original-source null/quality checks remain separate from cleaned-hour analysis.')
 d.add_page_break();h(d,'Task 4 point 2 Daily and hourly traffic charts')
 d.add_picture(str(R/'charts/daily_2015_2017.png'),width=Inches(6.5))
 p(d,'Daily averages use only observed hours on each date; missing days remain gaps. Comparisons should account for unequal hourly coverage, especially in 2015. Time-dependent patterns support calendar-aware staffing and modelling. A daily mean is not a daily total.')
 d.add_picture(str(R/'charts/hourly_2017.png'),width=Inches(6.4))
 p(d,'For 2017, group by Hour and average traffic_volume. Filter Year=2017 in the Power BI hourly visual. Daytime demand exceeds overnight demand, with pronounced commuter-period peaks. These describe volume rather than measured queue delay or traffic speed.')
 d.add_page_break();h(d,'Task 4 point 2 Weather and temperature charts')
 table(d,['Weather','Mean traffic','Observed hours'],[[r.weather_main,f'{r["mean"]:.2f}',r['count']] for _,r in w.iterrows()])
 p(d,'Hourly highest: Smoke, 4,443.00 (n=2). Lowest: Squall, 2,061.75 (n=4). Difference: 2,381.25. The highest categories are not robust rankings of causal weather effects. Raw-record comparison: Clouds 3,618.44975 versus Squall 2,061.75, difference 1,556.69975. Raw and hourly grain must not be mixed.')
 d.add_picture(str(R/'charts/temperature_traffic.png'),width=Inches(5.9))
 p(d,f'The point-density rendering shows broad volume variation at the same temperature and a weak positive linear relationship. For volume>5500, the full Celsius range is {temp.min():.2f} to {temp.max():.2f}; the central 80% is {temp.quantile(.1):.2f} to {temp.quantile(.9):.2f}. No narrow temperature band guarantees high traffic. Raw 0 K records and 9,831.3 mm rain are impossible-value outliers and repaired. Large traffic values within the observed range are not automatically errors; zero-volume hours are retained without independent outage evidence.')
 d.add_page_break();h(d,'Task 4 point 3 KPIs and interactive filters')
 table(d,['All-data KPI','Value'],[['Total hours analysed','40,575 distinct observed hours'],['Average traffic volume','3,290.65 vehicles per observed hour'],['Average temperature Celsius',f'{dset["Temperature Celsius"].mean():.2f} °C'],['Average temperature Kelvin',f'{dset.temp.mean():.2f} K']])
 p(d,'Use Hour range (0–23, Between), weather_main and Traffic Category slicers. They should filter every overview visual. Daily charts retain visual year filters 2015–2017 and hourly bars retain 2017, so each has its own analysis scope. KPI cards are all-data within slicer selections, not restricted to the hourly chart year unless an explicit page filter is added. Clear all slicers to reproduce the KPI figures above.')
 h(d,'Power BI delivery and verification status')
 p(d,'PowerBI/Traffic_Intelligence.pbip is a prepared native project with an embedded original CSV, full Power Query cleaning, model measures, two report pages, three KPI cards, three slicers, four required charts and summary tables. This version changes the report content version from 4.0.0 to 2.0.0 and uses standard hexadecimal page/visual identifiers as a compatibility correction. The definition.pbir connection version remains 4.0; these are different version fields. File and field checks do not prove Desktop rendering. A verified PBIX and native screenshots still require opening/refreshing the project in Power BI Desktop. Do not rename the source project to PBIX.')
 p(d,'The interactive Traffic_Dashboard.html opens directly in a browser and provides a usable companion. It is not a substitute claim for a native Power BI submission. If the project still fails to display pages, the separate Power BI Step Guide gives a fresh-Desktop route using the prepared CSV, which already contains Hour, Date, Year, Celsius and Traffic Category.')
 h(d,'Operational recommendations')
 p(d,'First prioritise coverage monitoring and time-of-day staffing. Trial travel timing recommendations inside permitted windows and check operational outcomes. Retain rare-weather sample counts and validate effects on additional data before weather-based policy. High volume alone does not establish congestion speed, journey time, safety or emission changes; collect these measurements before making such claims.')
 save(d,'Part_1_Worked_Answers.docx')
 # SIMPLE DESKTOP GUIDE
 d=new('Power BI Step Guide')
 p(d,'Use this guide for Part 1 on a Windows laptop. Keep the new package separate from earlier versions so the correct project is opened.')
 h(d,'Route A Open the prepared native project')
 for t in ['1 Download Part_1_Traffic_Analytics.zip and use Extract All. Open the extracted Part1_Traffic_Analytics folder.','2 Open PowerBI, then double-click Traffic_Intelligence.pbip. Keep Traffic.Report and Traffic.SemanticModel beside it.','3 The report should contain Traffic Intelligence and Annual and Data Quality page tabs. Use Home > Refresh to evaluate the embedded queries.','4 Select Traffic Intelligence for the four charts, three KPI cards and three slicers. Select Annual and Data Quality for the tables.','5 Check the hour/weather/category controls and compare the all-data KPI against 40,575 hours and mean traffic 3,290.65.','6 Use File > Save As and select Power BI report (.pbix). Capture native screenshots only after the report actually renders.']:
  p(d,t)
 p(d,'This corrects a likely report-format compatibility issue in the earlier file, but the new project still requires Desktop verification. If the tabs do not appear, use Route B rather than repeatedly dragging into an empty report.')
 h(d,'Route B Start a fresh report with prepared columns')
 for t in ['1 In Power BI Desktop select File > New. Confirm Page 1 appears.','2 Home > Get data > Text/CSV. Select data/Traffic_PowerBI_Ready.csv from the extracted package. Click Open, then Load in the preview window.','3 The Data pane should show Traffic_PowerBI_Ready. This file already has Hour, Date, Year, Temperature Celsius and Traffic Category. No new Hour formula is needed.','4 Select a clustered column chart. Add Hour to X-axis and traffic_volume to Y-axis. On traffic_volume choose Average. In the visual Filters pane add Year and select 2017.','5 Save the report with a new name, such as Traffic_Part1.pbix.']:
  p(d,t)
 d.add_page_break();h(d,'Build the remaining visuals in Route B')
 table(d,['Visual','Fields and settings'],[['Daily line chart','X Date as the date column (not hierarchy); Y traffic_volume Average; visual Year filter 2015, 2016, 2017.'],['Weather bars','Category weather_main; value traffic_volume Average; add record count in tooltip.'],['Temperature scatter','X Temperature Celsius; Y traffic_volume; Details date_time where available; use per-hour granularity or suitable aggregation.'],['Hours card','date_time with Count distinct.'],['Average traffic card','traffic_volume with Average.'],['Average temperature card','Temperature Celsius with Average.'],['Hour slicer','Hour; choose Between mode.'],['Weather slicer','weather_main; list or dropdown.'],['Category slicer','Traffic Category; list or dropdown.'],['Year summary table','Year set Don’t summarize; date_time Count distinct; traffic_volume Average and Sum.']])
 p(d,'Click a blank canvas area before inserting another visual. Otherwise a new icon can change the selected visual. If dragging is difficult, select a visual and use the field checkboxes, then verify its axis assignments. Selecting fields without a report page cannot create a chart.')
 h(d,'Power Query evidence required by the assignment')
 p(d,'The prepared CSV is an easy display fallback. To demonstrate the assignment’s raw-data Power Query work, use the native project’s TrafficRaw/TrafficHourly queries, or create them manually: Home > Transform data > Manage parameters > new Text parameter CsvPath pointing to data/Metro_Interstate_Traffic_Volume.csv. Create blank query TrafficRaw and paste PowerBI/TrafficRaw.m in Advanced Editor, then create TrafficHourly and paste TrafficHourly.m. Close and Apply. Add each measure in Measures.dax separately on TrafficHourly.')
 p(d,'In Power Query, enable Column quality and Column profile, and profile the entire dataset. Record 48,204 ×9 raw shape, zero blank source cells, literal holiday None as a valid value, the numeric/date/text types, duplicate and impossible-weather checks, hourly consolidation and the five derived fields. Keep raw-data profiling separate from the 40,575-hour output.')
 h(d,'What to submit')
 p(d,'Submit the SQL/database, worked statistical/probability results, the verified native Power BI report and the two-page insights report. The provided project is source, not a verified PBIX. A local Desktop save and native screenshots complete the remaining dashboard verification step. The HTML companion and static charts are useful review aids and must be labelled accurately.')
 save(d,'Power_BI_Step_Guide.docx')
if __name__=='__main__':run()
