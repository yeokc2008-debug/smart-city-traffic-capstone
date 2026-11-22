# Submission and verification status

Compared with the supplied capstone instructions, 22 November 2026.

## Part 1
- SQLite database integrity: OK. Raw table: 48,204 records. All 12 SQL statements executed successfully using Python SQLite.
- Descriptive and probability analysis, data-quality outputs, reports and Power BI project are included.
- `insights_report.pdf` is a two-page PDF exported from the included Word report.
- The packaged Power BI source is not the later manually corrected report. The user previously showed working visuals in Desktop after fixing the scatter plot, but the corrected PBIX was not available to include. Add it to `part1_data_analytics/powerbi/` and confirm slicers, chart filters and visual interactions.

## Part 2
- Bundled raw CSV, pipeline, features, visualizations, mini-app, four figures, log, README and report are present.
- Clean-run pipeline completed successfully on the raw CSV; 40,575 hourly rows and four figures were generated. Ten unit tests passed. The CLI wrapper's compare command passed; the tests cover the commands and invalid input.
- Original incremental Part 2 task commits are preserved in `part2_original_history.bundle`. Clone the bundle to review original history. Root commits document assembly of this portfolio, not the original chronology. No public GitHub repository has been created.

## Part 3
- Supervised, clustering, association mining, neural, SHAP results, MLflow records, model artifacts, API simulation, recommendation, monitoring, final and fairness reports are included. No accident data were provided; the classification target is a documented proxy.
- Fourteen packaged tests passed, including checks on saved metrics, model artifacts, recorded runs, API simulation, monitoring and recommendation. The local MLflow SQLite store contains 2 experiments, 10 runs and 10 model versions.
- An attempt to run the full Part 3 workflow with `--reuse-models` stopped because SHAP was not installed in the checking environment. MLflow was also not installed here, so a new MLflow run and UI could not be verified. Use the supplied environment instructions and rerun on a machine with the specified dependencies.
- The updated Task 6 notebook records the same model IDs, registry versions and metrics as the included model manifest; a complete execution of this later notebook has not been verified here.
- `responsible_ai_report.pdf` is an export of the detailed Bias and Fairness Report, which also discusses governance and sustainability.

## Before submitting
1. Add the final corrected PBIX from your laptop and verify it opens with all data and slicers.
2. Install the Part 3 environment and rerun the latest root notebook or `python run_all.py --reuse-models`, then run the full tests and inspect the MLflow UI if required. Existing saved results do not replace this check.
3. Check your instructor's required submission method; publish the root to GitHub only if requested. Include the original development history bundle. These local assembly commits are not proof that a remote repository exists.
4. The organization diagram is a suggested structure. Supporting files are included for reproducibility. Review reports and file paths after extraction.
