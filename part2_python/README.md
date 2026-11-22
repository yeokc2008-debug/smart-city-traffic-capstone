# Capstone Part 2 Traffic Analytics

## Jupyter version

Open **Capstone_Part2.ipynb** for the executed step-by-step notebook. See START_JUPYTER.md
for Windows setup. Install requirements-jupyter.txt to run it. The notebook uses the same
modules and source data; notebook-generated outputs go to notebook_outputs/.


Start with reports/Part_2_Step_by_Step_Guide.docx for the detailed walkthrough.
The two-page submission report is reports/Part_2_Methodology_and_Findings.docx.

## Run the project

Open a terminal inside capstone_part2. Python 3.11+ is recommended.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux instead: source .venv/bin/activate
python -m pip install -r requirements.txt
python pipeline.py
python app.py at "2017-06-15 08:00:00"
python app.py high --threshold 5500 --limit 5
python app.py compare
python app.py travel --day-type weekday --start 7 --end 10
python -m unittest discover -s tests -v
```

If activation is blocked, use `.venv\Scripts\python.exe` instead of `python`.
No download or API key is required: the original UCI compressed CSV is bundled.

## Structure

- pipeline.py: safe loading, schema validation, orchestration and persistence.
- cleaning.py: categories, timestamps, duplicates, outliers, holidays and hourly consolidation.
- feature_engineering.py: time, cyclical, weather, scaled features and labels.
- visualizations.py: four Matplotlib figures; summaries.py: numerical support.
- app.py: four CLI queries; logging_utils.py: configuration called by entry points only.
- data/raw/: original data, attributed in DATA_SOURCE.md.
- data/processed/: hourly CSV, feature CSV, audit, parameters and summary CSV/JSON files.
- outputs/figures/: final charts; outputs/verification/: tests, CLI and sensitivity evidence.
- reports/: detailed guide and short submission report.
- tests/: ten behaviour tests; pipeline.log and app.log: real sample execution trails.
- ../part2_original_history.bundle: original incremental Part 2 Git history, preserved separately.

## Processing decisions

Validate all nine columns before processing. Preserve holiday `None` via keep_default_na=False.
Standardise whitespace/case, parse exact hourly timestamps, remove exact duplicates, reject
missing/negative/fractional traffic targets and retain zero traffic without outage evidence.
Weather validation gates are temp 150–350 K, rain/snow 0–9000 mm and cloud cover 0–100.
Nonfinite/missing readings are also invalid. Rain's broad gate detects the assignment anomaly;
it is not a calibrated meteorological threshold. For each month, replace invalid values with a
median fitted through end-2016, using one first-source contribution per timestamp. Use the
fitting-period median if a month has no valid values; abort if an entire variable is unavailable.
Save parameters. Propagate holiday labels within observed dates only. Reject conflicting traffic
counts within an hour, then retain one weather record. Missing hours remain gaps.

Default weather priority, highest first:
`Squall > Thunderstorm > Snow > Rain > Drizzle > Fog > Mist > Haze > Smoke > Clouds > Clear > Unknown`.
Ties retain original source order. This explicit project convention reproduces 3133 positives;
the supplied discussion does not establish the full original priority order. It is not a validated
hazard scale. Rain/Drizzle can outrank low visibility without belonging to the risk-weather list.

| Selection rule | Positive hours | Share |
| --- | ---: | ---: |
| First record per hour | 2964 | 7.3050% |
| Documented severity order | 3133 | 7.7215% |

Selecting ANY risky weather in each hour is a different rule and yields 3917 positives.
Do not silently substitute it. Weather-category counts and means change with selection rules;
traffic quartiles and means do not, because traffic agrees within repeated timestamps.

```bash
python pipeline.py --collapse first --output-dir outputs/first/data --figures-dir outputs/first/figures --log outputs/first/pipeline.log
```

## Features and targets

Hour, weekday (Monday=0), weekend, date, month, year, holiday and Celsius are derived.
Hour sine/cosine use period 24, weekday period 7, month (month-1) period 12.
Weather has a fixed one-hot vocabulary including Unknown plus low-visibility/severe-weather flags.
Temperature Celsius and rainfall are scaled using (x - mean)/population_SD; fit through end-2016
and apply unchanged to later data. Parameters and predictor lists are in feature_metadata.json.

Full hourly quartiles are Q1=1248.5, Q2=3427, Q3=4952. Low <=Q1; Medium >Q1 and <=Q2;
High >Q2 and <=Q3; Severe >Q3. The quoted Q1=1248 is rounded/truncated.
High risk means traffic_volume >3427 AND selected weather in Thunderstorm, Snow, Squall,
Fog, Mist, Haze or Smoke. Exactly 3427 is not high risk. 3417 is an apparent typo.
Part 1 categories remain separate: Low <4500; Medium 4500–5500 inclusive; High >5500.
Part 1 congestion >5500 gives 6107 hours.

For Part 3 use only model_predictor_columns, excluding traffic_volume and every derived label
from classifier inputs. The proxy is not an actual accident outcome. For strict future holdout
assessment split chronologically FIRST and refit all preprocessing and label quartiles using only
training data. Full-hourly quartiles here implement the assignment's descriptive convention;
this Part 2 workflow does not claim an independently evaluated ML model.

## Actual results and figures

Raw 48204 x 9 -> remove 17 exact duplicates -> remove 7612 extra hourly records -> 40575 x 9.
Feature table: 40575 x 44. Ten temperature values and one rainfall reading are imputed.
11976 hours are absent inside the observed date span; no missing hours are invented.
Mean traffic 3290.65; median 3427; sample SD 1984.77; mean Celsius 8.23; correlation about 0.13954.
Weekday mean 3557.44 vs weekend 2623.93, subject to differing calendar/hour coverage.

1. Hourly day-type lines show weekday peaks at about 07:00 and 16:00, weekend midday peaks.
2. Weather bars show means and counts: Smoke 4443 (n=2), Squall 2061.75 (n=4). Orange means
   n<30, a display convention rather than a statistical significance threshold.
3. Temperature hexbin plot shows broad traffic spread and a weak linear relationship.
4. Traffic histogram shows spread with median and Q3. Ties mean quartile groups need not be equal-sized.

Annual totals depend on coverage; weather associations can be confounded by hour and season.
Volume is not speed, delay, accident risk or emissions. CLI travel queries rank historical volumes only.

## CLI reference

Global options --data, --log and --debug precede the command. `at` requires YYYY-MM-DD HH:00:00
and reports missing observations explicitly. `high` accepts finite nonnegative thresholds and
limits 1–100. `compare` returns means and counts. `travel` uses weekday/weekend and an inclusive
0–23 hour window. Invalid values log ERROR without a traceback and return 2. Parser syntax errors
use standard argparse usage messages. Pipeline failures return 1 with exception details in the log.

## Logging

Every application module uses logging.getLogger(__name__). Entry points invoke configuration;
imports do not attach handlers. Configuration uses a shared parent to route named module records
to console and UTF-8 file handlers; library processing functions never call root logging methods.
Format: timestamp | level | module | message. Logs append across runs and use the machine clock.

- DEBUG: monthly medians, scaling and quartile parameters. Enabled only with --debug.
- INFO: input arguments, loaded shape, stage shapes, saved file paths and completion.
- WARNING: numbers of rows dropped/modified/imputed, with reasons, per cleaning step.
- ERROR: a failed operation; pipeline errors include exception details as required.

Default logs: pipeline.log and app.log; override using --log PATH. Normal runs exclude DEBUG.
Only CLI answers use print(); internal progress always uses named loggers.

## Verification and GitHub

Ten tests passed: schema, hourly counts, both proxy counts, boundaries, scaling fit period,
cyclical wrap, invalid data, four CLI commands, bad inputs, missing-file failures and DEBUG suppression.
Evidence is in outputs/verification. Data and results are real, not synthetic.

The original incremental history is preserved in ../part2_original_history.bundle. The portfolio root has separate assembly commits. No GitHub remote has been published. To inspect original Part 2 task history, run `git clone ../part2_original_history.bundle part2_history_review` from this directory. To publish the complete portfolio, use the root repository, not a nested Part 2 repository. The example below applies only to a standalone Part 2 checkout:

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/capstone_part2.git
git push -u origin main
```

Extract hidden folders when using the portfolio repository and preserve the original history bundle.
