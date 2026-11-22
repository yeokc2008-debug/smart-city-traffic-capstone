# Smart City Traffic Intelligence Portfolio

This portfolio assembles Parts 1-3 from the Metro Interstate Traffic Volume capstone. Read SUBMISSION_CHECKLIST.md before submission. The assignment text is included in ASSIGNMENT_INSTRUCTIONS.txt.

## Contents

- `part1_data_analytics/`: SQLite source, SQL analyses, statistics and probability results, Power BI project, data and `insights_report.pdf`.
- `part2_python/`: executable pipeline and mini CLI, figures, example logs, tests, documentation and notebooks.
- `part3_machine_learning/`: saved models, notebooks, MLflow tracking, API, recommendation, monitoring, reports and `responsible_ai_report.pdf`.
- `part2_original_history.bundle`: the actual original Part 2 development commits. The root repository commits document portfolio assembly and are not represented as historical development of the project.
- `additional_prior_version/`: separately preserved prior work; this is not the authoritative implementation.

## Start

In Anaconda Prompt, change to `part2_python` or `part3_machine_learning` and follow that part's README, including environment setup. To run the mini-application from the Part 2 folder: `python cli_app/app.py compare`. For Part 3, the later `Capstone_Part3_Task6_Updated.ipynb` is located in the Part 3 root so its relative paths can resolve. The same notebook is also in `notebooks/` for organization, but launch the root copy from the Part 3 folder.

## Important context

The Power BI project in this package does not contain the subsequent manual scatter-plot fix made on the user's computer. Add the final saved PBIX to `part1_data_analytics/powerbi/`. That file has not been provided to this portfolio.

Part 1 and Parts 2/3 may choose different weather conditions when a timestamp has multiple weather rows. The selected-weather convention and data grain affect weather-specific results. Part 3 uses a documented proxy label, not actual accident data; its high classification scores do not indicate accident-prediction accuracy. The dataset includes observations through 2018; Part 1 annual comparisons are limited to 2012-2017, while Part 3 uses 2018 as a holdout.

The local Part 2 git bundle can be inspected with `git clone part2_original_history.bundle part2_history_review`. To publish a single repository, upload the root directory and preserve its separate development-history bundle. No GitHub remote has been created.
