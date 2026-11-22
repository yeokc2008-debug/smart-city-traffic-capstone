"""Run: python pipeline.py --input data/raw/Metro_Interstate_Traffic_Volume.csv.gz"""
import argparse
import hashlib
import json
import logging
from pathlib import Path
import sys
import pandas as pd
from cleaning import clean_data, validate_schema
from logging_utils import configure_logging
logger = logging.getLogger(__name__)

def load_raw(path):
    try:
        # Preserve literal holiday 'None'; genuine blank numeric cells are handled by cleaning.
        with (Path(path)).open('rb') as handle:
            df = pd.read_csv(handle, compression='gzip' if str(path).endswith('.gz') else None,
                             keep_default_na=False)
    except (OSError, ValueError, UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise ValueError(f'Cannot load CSV {path}: {exc}') from exc
    validate_schema(df)
    logger.info('Raw file loaded: %d rows x %d columns from %s', *df.shape, path)
    return df

def main(argv=None):
    parser = argparse.ArgumentParser(description='Reproducible hourly traffic analytics pipeline')
    parser.add_argument('--input', default='data/raw/Metro_Interstate_Traffic_Volume.csv.gz')
    parser.add_argument('--output-dir', default='data/processed')
    parser.add_argument('--figures-dir', default='outputs/figures')
    parser.add_argument('--log', default='pipeline.log')
    parser.add_argument('--collapse', choices=['severe', 'first'], default='severe')
    parser.add_argument('--fit-end', default='2016-12-31 23:59:59')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args(argv)
    try:
        configure_logging(args.log, args.debug)
        logger.info('Pipeline invoked with %s', vars(args))
        raw = load_raw(args.input)
        cleaned, audit, imputation = clean_data(raw, args.collapse, args.fit_end)
        from feature_engineering import engineer_features
        from visualizations import make_figures
        features, metadata = engineer_features(cleaned, args.fit_end)
        out = Path(args.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for name, frame in [('traffic_hourly.csv', cleaned), ('traffic_features.csv', features)]:
            frame.to_csv(out/name, index=False)
            logger.info('Saved %s: %d rows x %d columns', out/name, *frame.shape)
        audit['input_sha256'] = hashlib.sha256(Path(args.input).read_bytes()).hexdigest()
        metadata['imputation'] = imputation
        for name, obj in [('audit.json', audit), ('feature_metadata.json', metadata)]:
            (out/name).write_text(json.dumps(obj, indent=2), encoding='utf-8')
            logger.info('Saved %s', out/name)
        make_figures(features, args.figures_dir)
        from summaries import write_summaries
        write_summaries(features, out)
        logger.info('Pipeline completed successfully')
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, ImportError) as exc:
        if logging.getLogger().handlers:
            logger.error('Pipeline failed: %s', exc, exc_info=True)
        else:
            sys.stderr.write(f'ERROR: Cannot configure pipeline logging: {exc}\n')
        return 1

if __name__ == '__main__':
    sys.exit(main())
