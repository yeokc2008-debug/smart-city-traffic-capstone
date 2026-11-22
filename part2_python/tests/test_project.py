"""Behaviour tests for data correctness, leakage boundaries, and CLI failures."""
import contextlib
import io
import json
import logging
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import numpy as np
import pandas as pd
from cleaning import clean_data, validate_schema, RISK_WEATHER
from feature_engineering import engineer_features
from pipeline import load_raw

class ProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=load_raw('data/raw/Metro_Interstate_Traffic_Volume.csv.gz')
        cls.hourly,cls.audit,_=clean_data(cls.raw)
        cls.features,cls.meta=engineer_features(cls.hourly)
    def test_schema_rejects_before_cleaning(self):
        with self.assertRaisesRegex(ValueError,'Missing expected columns'):
            clean_data(self.raw.drop(columns='temp'))
    def test_hourly_grain_and_counts(self):
        self.assertEqual(len(self.hourly),40575)
        self.assertTrue(self.hourly.date_time.is_unique)
        self.assertEqual(self.audit['exact_duplicates_dropped'],17)
        self.assertEqual(self.audit['temp_imputed'],10)
        self.assertEqual(self.audit['rain_1h_imputed'],1)
        self.assertEqual(self.audit['missing_hours_within_span'],11976)
    def test_collapse_sensitivity(self):
        first,_,_=clean_data(self.raw,collapse='first')
        self.assertEqual(int(((first.traffic_volume>3427)&first.weather_main.isin(RISK_WEATHER)).sum()),2964)
        self.assertEqual(int(self.features.high_risk.sum()),3133)
    def test_targets_and_boundaries(self):
        x=self.hourly.iloc[:7].copy()
        x['traffic_volume']=[0,1248,1249,3427,3428,4952,4953]
        x['weather_main']='Fog'
        x['rain_1h']=[0,.1,.2,.3,.4,.5,.6]
        out,meta=engineer_features(x)
        expected=(out.traffic_volume>out.traffic_volume.median()).astype(int)
        np.testing.assert_array_equal(out.high_risk,expected)
        self.assertEqual(meta['quartiles']['q2'],3427)
        self.assertFalse(set(meta['model_predictor_columns']) & set(meta['exclude_from_predictors']))
    def test_scaling_fitted_only_on_reference_period(self):
        ref=self.features.loc[self.features.date_time<=pd.Timestamp(self.meta['fit_end'])]
        self.assertAlmostEqual(ref.temp_c_scaled.mean(),0,places=10)
        self.assertAlmostEqual(ref.temp_c_scaled.std(ddof=0),1,places=10)
        self.assertAlmostEqual(ref.rain_1h_scaled.mean(),0,places=10)
    def test_hour_cycle_wraps(self):
        p=np.array([23,0,12]);a=np.c_[np.sin(2*np.pi*p/24),np.cos(2*np.pi*p/24)]
        self.assertLess(np.linalg.norm(a[0]-a[1]),np.linalg.norm(a[0]-a[2]))
    def test_invalid_values_and_missing_dates(self):
        x=self.raw.iloc[:5].copy()
        x.loc[x.index[0],'date_time']='bad date'
        x.loc[x.index[1],'temp']=0
        with self.assertLogs('cleaning',level='WARNING') as captured:
            out,_,_=clean_data(x)
        self.assertEqual(len(out),4)
        self.assertTrue(out.temp.between(150,350).all())
        self.assertTrue(any('imputed' in s for s in captured.output))
    def test_cli_commands_and_errors(self):
        cases=[(['at','2017-06-15 08:00:00'],0),(['high','--limit','2'],0),
               (['compare'],0),(['travel','--start','7','--end','10'],0),
               (['at','not-a-date'],2),(['travel','--start','25'],2),
               (['high','--limit','oops'],2)]
        with tempfile.TemporaryDirectory() as directory:
            for args,expected in cases:
                result=subprocess.run([sys.executable,'app.py','--log',str(Path(directory)/'app.log')]+args,capture_output=True,text=True)
                self.assertEqual(result.returncode,expected,result.stderr)
                self.assertNotIn('Traceback',result.stderr)
    def test_missing_file_logs_error_and_fails_gracefully(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'error.log'
            result=subprocess.run([sys.executable,'pipeline.py','--input','missing.csv','--log',str(path)],capture_output=True,text=True)
            self.assertEqual(result.returncode,1)
            self.assertIn('ERROR',path.read_text())
            # Error details belong in the audit log, as required by the assignment.
    def test_debug_hidden_in_normal_run(self):
        text=Path('pipeline.log').read_text()
        self.assertNotIn('| DEBUG |',text)
        for name in ['01_hourly_day_type.png','02_weather_traffic.png','03_temperature_traffic.png','04_traffic_distribution.png']:
            self.assertTrue((Path('outputs/figures')/name).is_file())

if __name__=='__main__':
    unittest.main()
