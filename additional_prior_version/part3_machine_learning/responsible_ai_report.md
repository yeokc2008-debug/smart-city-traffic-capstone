# Responsible and Sustainable AI Report

## Bias and fairness

The data covers one westbound I-94 location near Minneapolis–St Paul and cannot represent other roads, directions, neighbourhoods or traveller groups. Coverage varies over time, and weather observations can repeat at one timestamp. The artificial `high_risk` label is not accident ground truth: it encodes an assumption that upper-half traffic and severe or low-visibility weather imply risk. A classifier may therefore reproduce that rule while learning nothing about actual collisions. Performance should be audited by year, hour, weather and season; sparse severe-weather groups can have unstable error rates.

## Governance

Outputs should support human traffic planners, not automatically close roads, issue penalties or make safety claims. Before real use, obtain accident and exposure data, document ownership and retention, validate on later time periods and other corridors, establish approval and incident-response roles, monitor drift and false-negative rates, and provide appeal and override mechanisms.

## Sustainability

Linear models and compact random forests are preferred when their performance is close to larger models because they train faster, use less energy and are easier to explain. The neural network is intentionally small. Retraining should be triggered by verified drift or scheduled evidence needs rather than continuously, and experiment artifacts should be retained selectively.
