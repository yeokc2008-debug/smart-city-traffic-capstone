# Standard-library deployment simulation: POST /predict with JSON feature values.
import json,logging
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
import joblib,pandas as pd
logger=logging.getLogger(__name__); logging.basicConfig(level=logging.INFO); MODEL=joblib.load(Path(__file__).parent/'models/random_forest_regression.joblib')
class Handler(BaseHTTPRequestHandler):
 def do_POST(self):
  try:
   n=int(self.headers.get('Content-Length',0)); payload=json.loads(self.rfile.read(n)); row=pd.DataFrame([payload]); pred=float(MODEL.predict(row)[0]); body=json.dumps({'traffic_volume_prediction':round(pred,1)}).encode(); self.send_response(200)
  except Exception as e: logger.error('Prediction failed',exc_info=True); body=json.dumps({'error':str(e)}).encode(); self.send_response(400)
  self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(body)
if __name__=='__main__': logger.info('Serving on port 8000'); HTTPServer(('127.0.0.1',8000),Handler).serve_forever()
