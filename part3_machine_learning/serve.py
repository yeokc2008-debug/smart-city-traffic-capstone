"""Local API entry point; no production hosting claim."""
import logging
from config import ROOT
from logging_utils import configure_logging
logger=logging.getLogger(__name__)
if __name__=='__main__':
    configure_logging(ROOT/'deployment.log')
    import uvicorn
    logger.info('Starting teaching API on 127.0.0.1:8000')
    uvicorn.run('api:app',host='127.0.0.1',port=8000)
