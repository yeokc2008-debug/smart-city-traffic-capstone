"""Run all Part 3 tasks. Notebook uses --reuse-models to inspect shipped artifacts."""
import argparse,json,logging,sys,time
from pathlib import Path
import joblib
import pandas as pd
from threadpoolctl import threadpool_limits
from config import ROOT
from logging_utils import configure_logging
logger=logging.getLogger(__name__)

def run(reuse_models=False):
    from data_features import load_data
    from modeling import train_models
    from unsupervised import run_unsupervised
    from explainability import explain_demand
    from evaluation import evaluate_outputs
    from recommendation import save_examples
    from api import simulate_api
    from monitoring import simulate_monitoring
    (ROOT/'outputs/figures').mkdir(parents=True,exist_ok=True)
    (ROOT/'models').mkdir(exist_ok=True)
    with threadpool_limits(limits=2):
        df,x=load_data()
        if reuse_models:
            results=pd.read_csv(ROOT/'outputs/model_comparison.csv')
            models={name:joblib.load(ROOT/'models'/f'{name}.joblib') for name in results.model}
            selection=json.loads((ROOT/'models/selection.json').read_text())
            predictions=pd.read_csv(ROOT/'outputs/test_predictions.csv')
            logger.info('Loaded existing trained models; training skipped explicitly')
        else:results,models,selection,predictions=train_models(df,x)
        run_unsupervised(df)
        explain_demand(df,x,models)
        evaluate_outputs(df,results,models,selection,predictions)
        save_examples();simulate_api();simulate_monitoring(df,x,models,selection)
    logger.info('All seven task workflows completed')
    return df,x,results,models,selection

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--reuse-models',action='store_true');p.add_argument('--debug',action='store_true');a=p.parse_args(argv)
    configure_logging(ROOT/'part3.log',a.debug)
    try:run(a.reuse_models);return 0
    except Exception as exc:
        # Entry-point boundary: capture unexpected failures with their details; no bare except.
        logger.error('Part 3 failed: %s',exc,exc_info=True);return 1

if __name__=='__main__':sys.exit(main())
