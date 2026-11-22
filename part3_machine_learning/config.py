"""Shared reproducibility and label contract."""
import logging
from pathlib import Path
logger=logging.getLogger(__name__)
ROOT=Path(__file__).resolve().parent
SEED=42
TRAIN_END='2016-12-31 23:59:59'
VALID_END='2017-12-31 23:59:59'
RISK_WEATHER={'Thunderstorm','Snow','Squall','Fog','Mist','Haze','Smoke'}
WEATHERS=['Squall','Thunderstorm','Snow','Rain','Drizzle','Fog','Mist','Haze','Smoke','Clouds','Clear','Unknown']
# Frozen assignment target thresholds, independent of model selection.
LABEL_QUARTILES=[1248.5,3427.0,4952.0]
