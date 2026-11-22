# Smart City Traffic Intelligence Capstone

End-to-end analysis of westbound I-94 hourly traffic near Minneapolis–St Paul. The repository covers SQL/statistics/probability and Power BI preparation, a logged Python pipeline and CLI, and machine-learning, clustering, explainability, recommendation, deployment and monitoring simulations.

## Quick start

```bash
python part2_python/pipeline.py --input data/Metro_Interstate_Traffic_Volume.csv
python part2_python/mini_app.py summary
python part3_machine_learning/train_models.py
python part3_machine_learning/recommend.py --day-type weekday --weather Clear
python part3_machine_learning/monitor.py
```

Run `python run_all.py` to reproduce the main pipeline, figures, analytics and models. Python 3.10+ is recommended. Install packages with `pip install -r requirements.txt`.

## Structure

- `data/`: raw and processed data
- `part1_data_analytics/`: SQLite/SQL, results, Power BI field guide and insights
- `part2_python/`: cleaning, features, visualisations, CLI, report and logs
- `part3_machine_learning/`: supervised/unsupervised models, neural network, explainability, experiment tracking, API mock-up, recommendation, monitoring, responsible AI report

## Important limitations

The source covers one westbound corridor, not an entire city or route network. Multiple rows can share a timestamp because weather observations are repeated; only exact duplicate rows are removed. No accident dataset was supplied. `high_risk` is a teaching proxy combining upper-half congestion with severe/low-visibility weather and must not be presented as actual accident probability. Holiday blanks mean `None`, not missing data.

## Logging

Entry points write timestamp, level, module and message to console and `part2_python/pipeline.log`. DEBUG records thresholds; INFO records normal milestones; WARNING records recoverable cleaning changes; ERROR records failures preventing completion. Each module uses `logging.getLogger(__name__)`.

## GitHub submission

Create a public repository (simplest for grading), verify no secrets are present, then commit incrementally. Suggested commits: initial structure; Part 1 SQL; pipeline; features and figures; CLI; supervised models; clustering and explainability; deployment and monitoring; reports. This supplied folder is not pre-committed so that your commit history honestly reflects your own work.
