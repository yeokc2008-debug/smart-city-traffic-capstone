# Capstone Part 3 Machine Learning and AI

## Purpose and proxy disclosure

This project estimates hourly traffic volume and a **documented assignment proxy label** on a
single westbound I-94 corridor. **No real accident dataset was sourced. No model predicts actual
accidents or calibrated accident probability.** The labels are a deterministic traffic/weather rule.
High proxy classification scores must not be presented as evidence of safety prediction skill.

Use **Anaconda and Jupyter**; VS Code is not needed. The main notebook is `Capstone_Part3.ipynb`.
Keep it beside the Python scripts and data folders. The notebook includes saved actual results.

## Open in Anaconda

1. Extract ALL files from capstone_part3.zip to a folder.
2. In Anaconda Prompt change to that extracted folder.
3. Create a dedicated environment (recommended Python 3.12):

```text
conda env create -f environment.yml
conda activate capstone_part3
python -m jupyterlab Capstone_Part3.ipynb
```

Alternatively, install requirements-jupyter.txt in an existing compatible environment:

```text
python -m pip install -r requirements-jupyter.txt
```

Launch Jupyter from that same environment in Anaconda Navigator, browse to the folder and open
Capstone_Part3.ipynb. Select the matching kernel, then Run > Run All Cells. The default notebook
loads the included trained models and re-executes downstream tasks; set RETRAIN_MODELS=True
near the start to train all models and create new MLflow runs. Reruns append logs and model versions.

Do not install packages into an unrelated Python environment. Pinned dependencies describe the
execution environment. Package installation needs internet; the bundled data and analysis do not.
If a model cannot load because scikit-learn versions differ, use the pinned environment or retrain.
Only load the supplied trusted joblib artifacts; arbitrary pickle/joblib files can execute code.

## Tasks and project structure

| Task | Implementation | Main evidence |
| --- | --- | --- |
| 1 Supervised models | modeling.py, data_features.py | model_comparison.csv; selected serialized models |
| 2 K-means and association rules | unsupervised.py | cluster profiles, assignments, rules and support counts |
| 3 Neural demand prediction and SHAP | DenseDemandModel in modeling.py; explainability.py | neural history, SHAP values and importance |
| 4 Advanced AI | MLflow tracking and registry in modeling.py | mlflow.db, mlartifacts/, model_versions.json |
| 5 Timing recommendations | recommendation.py | recommendations.json |
| 6 Deployment and monitoring | api.py, serve.py, monitoring.py | API simulation, monitoring JSON and HTML dashboard |
| 7 Responsible AI | evaluation.py; reports/ | fairness slices and the bias/fairness report |

- config.py: paths, seed, weather vocabulary, split and frozen label definitions.
- part2_cleaning.py: reused Part 2 cleaning and primary-weather priority.
- data/: original UCI compressed CSV and prepared hourly data.
- models/: five supervised models, K-means and selection metadata.
- outputs/: computed metrics, predictions, rules, figures, audit, API and monitoring evidence.
- logging_utils.py: logging configured only by entry points.
- portable_tracking.py: updates this project's own MLflow artifact URIs after extraction.
- tests/: fourteen behaviour tests; outputs/test_results.txt contains actual execution evidence.
- reports/Final_Capstone_Report.docx: methods and findings for all seven Part 3 tasks, with Part 1/2 context.
- reports/Bias_and_Fairness_Report.docx: coverage, proxy risks, measured slices, governance and sustainability.
- DATA_SOURCE.md: attribution; requirements files and environment.yml: dependencies.

The notebook contains the step-by-step analysis. Companion scripts are the reusable implementations.
The source data and Python modules are needed to rerun the notebook; an .ipynb alone is insufficient.

## Data contract and split

The original source has 48204 x 9 records. Remove 17 exact duplicates, repair 10 zero-Kelvin
values and one rainfall reading of 9831.3 mm using monthly medians fitted through end-2016,
propagate holiday markers within observed dates, and consolidate 7612 additional weather records.
Result: 40575 unique observed hours. Keep legitimate zero traffic, preserve literal holiday None,
and do not invent the 11976 hours missing within the first-to-last observation span.

Weather priority, highest first:
`Squall > Thunderstorm > Snow > Rain > Drizzle > Fog > Mist > Haze > Smoke > Clouds > Clear > Unknown`.
Ties use original file order. This explicit project convention reproduces the approved 3133 positives;
it is not a validated physical hazard ordering. Part 1 weather figures must be reconciled if that
part used a different selected-weather rule. Selecting ANY risky weather in an hour is a different rule.

| Split | Period | Hours | Proxy positives |
| --- | --- | ---: | ---: |
| Training | 2012 through 2016 | 25329 | 1775 |
| Validation | 2017 | 8713 | 764 |
| Final test | January–September 2018 | 6533 | 594 |

Imputation, scaling and supervised parameter fitting use training data only. Candidate model selection,
classification thresholds and neural stopping use 2017 only. 2018 is held out from model selection.
The models are observed-weather, same-hour condition estimators; they are not evaluated as multi-hour
forecasts using weather forecasts. Predictors contain no traffic volume, traffic category or risk label.

Features shared by both supervised tasks: hour/weekday/weekend, holiday flag, temperature and
precipitation/cloud cover, fixed one-hot weather, severe/visibility flags, and sine/cosine pairs for
hour, weekday and month (28 predictors). StandardScaler is fitted inside each training pipeline.

### Label convention

Frozen assignment quartiles: Q1=1248.5, Q2=3427, Q3=4952. Low <=Q1, Medium >Q1 through Q2,
High >Q2 through Q3, Severe >Q3. Proxy positive = volume >3427 AND selected weather in
Thunderstorm/Snow/Squall/Fog/Mist/Haze/Smoke. There are 3133 positives (7.7215%). First-row selection
would give 2964. The number 3417 in the discussion is an apparent typo; the stated median is 3427.
Part 1's separate congestion threshold >5500 is not this target.

These thresholds are frozen from the assignment/Part 2 definition, not tuned using model test scores.
They were originally descriptive full-data quartiles; this is a label-contract choice, not a claim
that thresholds were learned exclusively from training data. Training-only quartiles are recorded in
data_audit.json for transparency. A genuinely prospective study must predefine label thresholds or
learn them using training data before evaluating on unseen data.

## Actual model results

| Demand model | Validation MAE | 2018 test MAE | Test R-squared |
| --- | ---: | ---: | ---: |
| Ridge baseline | 797.42 | 799.31 | 0.7381 |
| Random forest | 239.27 | 229.81 | 0.9610 |
| Neural network | 377.34 | 349.96 | 0.9351 |

The forest is selected using lowest validation MAE, not test scores. Model outputs are clipped at
zero to enforce nonnegative vehicle counts. Models retain the training-only fit, with no final
train-plus-validation refit, so validation and test results correspond to the same artifacts.

| Proxy classifier | Test accuracy | Precision | Recall | F1 | ROC AUC | PR-AUC/AP |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Logistic baseline | 0.9787 | 0.8292 | 0.9646 | 0.8918 | 0.9939 | 0.9231 |
| Random forest | 0.9848 | 0.8634 | 0.9899 | 0.9224 | 0.9967 | 0.9488 |

Select the classifier using validation average precision; choose its operating threshold using
validation F1. Thresholds are frozen for final testing. Report AP as the precision–recall summary,
not trapezoidal PR area. Scores are uncalibrated, particularly with class weighting. High ROC AUC
largely reflects a simple deterministic proxy and cannot establish accident prediction performance.

## Unsupervised analysis and explainability

K-means fits StandardScaler and k=3/4/5 on training-only traffic-condition inputs: hour sine/cosine,
ordinal weather priority and traffic volume. Choose k by training-sample silhouette (seeded n=2000).
Selected k=5, silhouette about 0.3925. Name clusters from traffic intensity and inspect time/weather
profiles. These are descriptive groups, not accident clusters. Ordinal weather spacing and the small
k search can affect the result. Arithmetic mean hour is shown for reference but is unreliable for
clusters spanning midnight; use cyclic plots and assignments for time interpretation.

Association mining exhaustively enumerates antecedents of 1–3 distinct fields (time period, day type,
weather), with congestion category only as consequent. Minimum antecedent count 50, joint count 30,
support .005 and lift >1. Rank by TRAINING lift; test confidence/lift are diagnostic. 127 rules meet
these gates. The top rule is weekend overnight Snow -> Low: support .00505, confidence .9922,
lift 3.8996 (128 joint training hours; 40 test antecedent hours). It is association, not causation.

The neural regressor has hidden layers 64/32/16 with ReLU/Adam, training-only X/y scalers and
manual epoch checkpoints selected on chronological 2017 validation. No random internal validation
split is used. Best epoch 12 of 24 run epochs, with patience 12. No LSTM or fabricated continuous
sequence is claimed. A tabular neural network is one of the task's allowed options.

SHAP TreeExplainer explains the comparable random-forest demand model on a seeded 150-hour test
sample. It does not explain neural weights. RF/neural prediction disagreement averages 286.53
vehicles/hour; R-squared agreement against neural predictions is .95594. SHAP is model attribution,
not causal explanation. Time encodings are correlated, so attribution can be shared across columns.

## MLflow and model versions

SQLite tracking is in mlflow.db; artifacts in mlartifacts/. Real runs log model parameters,
validation/test metrics, fit time, artifact size, schema and serialized joblib models. Two registered
families, TrafficVolume and ProxyRisk, have actual registry versions; model_versions.json maps the
latest five candidates to registry versions, run IDs and local artifacts. Repeated training creates
additional real runs and registry versions. Registry artifacts are joblib, not managed MLflow pyfunc
models. FastAPI loads the locally selected artifacts. No public registry or hosted deployment is claimed.

After moving the folder, run from the project root:

```text
python portable_tracking.py
```

The notebook also calls this helper. It updates this project's local artifact URI records so they
point to the extracted mlartifacts folder. This is not a migration of external tracking data.
The notebook queries the SQLite tracking store directly through MLflow and displays run metrics.
For an optional web UI, install the full MLflow distribution (the lightweight tracking package is
sufficient for the notebook):

```text
python -m pip install mlflow==3.17.2
python portable_tracking.py
python -m mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

Open http://127.0.0.1:5000 locally. Browser-based MLflow UI hosting is not part of the tested simulation.
Experiment tracking adds traceability and comparison; it does not guarantee reproducibility across
libraries/hardware, correct labels, or valid deployment. CPU fit durations are environment-specific.

## Recommendation engine

```python
from recommendation import recommend
result = recommend('2018-06-18', 'Clear', start=7, end=12)
result['recommendation']
```

Uses training-only historical day-type/hour/weather means (minimum weather support n=20; otherwise
falls back to day-type/hour) and selected-model predictions. Other weather inputs use historical
medians. Rank one-hour departure windows by the equal-weight mean of historical and predicted
volume; this weighting is a documented heuristic, not a validated optimisation objective. The example
selects 10:00–11:00, historical mean 4458, n=211, model estimate 4389. A Snow example is deliberately
hypothetical and may be seasonally unusual. Supply the holiday flag explicitly when appropriate.
This dataset has one corridor, not route alternatives. Lower volume does not guarantee less delay,
safety or lower emissions. Severe weather triggers an explicit caution in the text.

## Deployment and monitoring simulation

```text
python serve.py
```

Open http://127.0.0.1:8000/docs locally. POST /predict accepts an exact source-local hourly datetime,
known weather, temperature Kelvin, rainfall, snowfall, cloud cover and optional holiday flag. It returns
predicted volume, uncalibrated proxy score, label and model version IDs. It rejects invalid timestamps,
unknown weather, impossible values and supplied traffic targets with HTTP 422. See api_simulation.json
for actual request/response evidence from in-process FastAPI TestClient. A live network listener was
not needed for that test and is not claimed as verified production hosting.

Monitoring uses fixed heuristic gates: population stability index >.20 on temperature/cloud/hour or
MAE >1.25 times the 2017 reference. Baseline self-comparison passes; observed 2018 comparison passes;
synthetic +15 Celsius feature shift and +2000 vehicle prediction error offset alert. The injected
scenario is explicitly synthetic, not a real production incident. The HTML monitoring dashboard is
local and static. PSI can react to seasonal coverage; delayed error monitoring requires actual labels.
PASS means no configured threshold was exceeded, not safety certification.

## Logging and reproducibility

Every project module uses logging.getLogger(__name__). Only entry points configure console and UTF-8
file handlers. Format is timestamp | level | module | message. part3.log stores pipeline events,
deployment.log local serving events, and notebook.log notebook milestones. Logs append across runs.

- DEBUG: internal epoch/parameter details; enabled by --debug.
- INFO: loading, training, selected models, figures and model saves.
- WARNING: rows dropped/imputed, sparse recommendation support and drift alerts.
- ERROR: failures caught by entry-point boundaries with exception details.

No print() is used for internal status. Notebook displays are user-facing results. To rerun:

```text
python run_all.py
python run_all.py --reuse-models
python run_all.py --debug
python -m unittest discover -s tests -v
```

Fourteen tests cover labels/boundaries, chronological partitions, target exclusion, scaler scope,
metric recomputation, validation selection, API schema, recommendations, monitoring, supported rules,
SHAP/neural artifacts, actual MLflow registry records and fairness denominators.

The portfolio root has local assembly commits; GitHub publication has not been performed. A folder is an allowed
deliverable. Review and publish to your own account if your lecturer specifically requests a URL.

## Responsible use and sustainability

Coverage is uneven, including a long 2014–2015 gap and incomplete 2018. One westbound sensor does
not represent a whole city. Rare weather samples are too small for reliable subgroup conclusions.
No demographic attributes exist, so this is condition-slice auditing, not demographic fairness proof.
Snow test demand MAE is 540.8 across 516 hours; night recall is .50 with only four positives.
Weekend test precision is .6667 versus .9134 on weekdays; investigate false alerts and support before
operational use. Blank recall means there were no true positives in that weather group, not perfect
performance. The reports describe measured errors and limitations in detail.

Use operator review, data/label ownership, versioned approvals, calibration, shadow deployment,
rollback and seasonally matched monitoring before real-world decisions. Do not automate enforcement
or safety restrictions from this proxy. The forest offers better held-out demand accuracy here; the
neural model does not show additional predictive value on this comparison. Small CPU models and
cached artifacts reduce unnecessary retraining. No carbon footprint or emissions saving was measured.

## Sources

Hogue, J. (2019). Metro Interstate Traffic Volume, UCI Machine Learning Repository.
https://doi.org/10.24432/C5X60B — CC BY 4.0.

Implementation references: https://scikit-learn.org/stable/ ; https://shap.readthedocs.io/ ;
https://mlflow.org/docs/latest/ ; https://fastapi.tiangolo.com/ .
