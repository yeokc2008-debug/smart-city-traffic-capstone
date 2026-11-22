"""Resolve this project's own MLflow artifact paths after ZIP extraction."""
import logging,sqlite3
from config import ROOT
logger=logging.getLogger(__name__)
def relocate_tracking():
    if not (ROOT/'mlflow.db').exists():return 0
    changed=0
    with sqlite3.connect(ROOT/'mlflow.db') as c:
        for run_id,uri in c.execute('SELECT run_uuid,artifact_uri FROM runs').fetchall():
            new=(ROOT/'mlartifacts'/run_id/'artifacts').as_uri()
            if uri!=new:
                c.execute('UPDATE runs SET artifact_uri=? WHERE run_uuid=?',(new,run_id));changed+=1
        c.execute('UPDATE experiments SET artifact_location=? WHERE name=?',((ROOT/'mlartifacts').as_uri(),'Capstone_Part3_Mobility'))
    logger.info('Resolved MLflow artifact paths; updated %d run URIs',changed)
    return changed
if __name__=='__main__':
    from logging_utils import configure_logging
    configure_logging(ROOT/'part3.log');relocate_tracking()
