import unittest,json,sqlite3,logging
import numpy as np
import pandas as pd
import joblib
from fastapi.testclient import TestClient
from sklearn.metrics import mean_absolute_error
from config import ROOT,RISK_WEATHER
from data_features import build_features,categories
from api import app
from recommendation import recommend
from monitoring import psi
logger=logging.getLogger(__name__)
class Part3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df=pd.read_csv(ROOT/'data/traffic_hourly.csv',keep_default_na=False,parse_dates=['date_time'])
        cls.x=build_features(cls.df)
        cls.selection=json.loads((ROOT/'models/selection.json').read_text())
    def test_unique_hours_and_proxy_count(self):
        self.assertEqual(len(self.df),40575);self.assertTrue(self.df.date_time.is_unique)
        self.assertEqual(self.df.high_risk.sum(),3133)
    def test_proxy_boundaries(self):
        self.assertEqual(list(categories(np.array([1248,1249,3427,3428,4952,4953]))),['Low','Medium','Medium','High','High','Severe'])
        expected=(self.df.traffic_volume.gt(3427)&self.df.weather_main.isin(RISK_WEATHER)).astype(int)
        np.testing.assert_array_equal(expected,self.df.high_risk)
    def test_chronological_split(self):
        groups=[self.df.loc[self.df.split.eq(s)] for s in ['train','validation','test']]
        self.assertEqual([len(g) for g in groups],[25329,8713,6533])
        self.assertLess(groups[0].date_time.max(),groups[1].date_time.min())
        self.assertLess(groups[1].date_time.max(),groups[2].date_time.min())
    def test_predictors_exclude_targets(self):
        self.assertFalse(set(self.x.columns)&{'traffic_volume','high_risk','congestion_category','split','date_time'})
        self.assertEqual(self.x.shape[1],28)
        self.assertTrue({'hour_sin','hour_cos','dow_sin','dow_cos','is_holiday'}<=set(self.x.columns))
    def test_train_only_scaling(self):
        model=joblib.load(ROOT/'models/ridge_v1.joblib')
        np.testing.assert_allclose(model.named_steps['standardscaler'].mean_,self.x.loc[self.df.split.eq('train')].mean(),atol=1e-10)
    def test_saved_metrics(self):
        p=pd.read_csv(ROOT/'outputs/test_predictions.csv');r=pd.read_csv(ROOT/'outputs/model_comparison.csv').set_index('model')
        self.assertAlmostEqual(mean_absolute_error(p.traffic_volume,p.forest_reg_v2),r.loc['forest_reg_v2','test_mae'],places=7)
    def test_validation_selection(self):
        t=pd.read_csv(ROOT/'outputs/model_comparison.csv')
        best=t.loc[t.task.eq('regression')].sort_values('validation_mae').iloc[0].model
        self.assertEqual(best,self.selection['regression'])
    def test_api_and_input_validation(self):
        body={'date_time':'2018-06-18T08:00:00','weather_main':'Clear','temp':288.15}
        with TestClient(app) as c:
            r=c.post('/predict',json=body);self.assertEqual(r.status_code,200)
            self.assertGreaterEqual(r.json()['predicted_vehicles_per_hour'],0)
            self.assertFalse(r.json()['actual_accident_prediction'])
            for bad in [{'date_time':'bad'},{'temp':0},{'weather_main':'Hurricane'},{'traffic_volume':6000},{'date_time':'2018-06-18T08:30:00'}]:
                self.assertEqual(c.post('/predict',json={**body,**bad}).status_code,422)
    def test_recommendation(self):
        r=recommend('2018-06-18','Clear',7,12)
        self.assertTrue(all(7<=x['hour']<12 for x in r['candidates']))
        self.assertIn('10:00',r['recommendation'])
        with self.assertRaises(ValueError):recommend('2018-06-18','Clear',12,7)
    def test_monitoring(self):
        r=json.loads((ROOT/'outputs/monitoring.json').read_text())
        self.assertEqual(r['baseline_self_comparison']['status'],'PASS');self.assertEqual(r['synthetic_stress']['status'],'ALERT')
        a=np.linspace(0,1,1000);self.assertAlmostEqual(psi(a,a),0);self.assertGreater(psi(a,a+10),.2)
    def test_association_support(self):
        r=pd.read_csv(ROOT/'outputs/association_rules.csv')
        self.assertTrue((r.support>=.005).all());self.assertTrue((r.antecedent_n>=50).all())
        self.assertFalse(r.antecedent.str.contains('congestion').any())
    def test_shap_and_neural(self):
        i=pd.read_csv(ROOT/'outputs/shap_importance.csv');self.assertEqual(len(i),28)
        self.assertTrue((i.mean_absolute_shap_vehicles>=0).all())
        m=joblib.load(ROOT/'models/neural_v3.joblib');self.assertEqual(m.net.hidden_layer_sizes,(64,32,16))
        self.assertLessEqual(m.best_epoch,len(m.history))
    def test_mlflow_versions(self):
        versions=json.loads((ROOT/'outputs/model_versions.json').read_text());self.assertEqual(len(versions),5)
        with sqlite3.connect(ROOT/'mlflow.db') as c:
            self.assertGreaterEqual(c.execute('select count(*) from runs').fetchone()[0],5)
            self.assertGreaterEqual(c.execute('select count(*) from model_versions').fetchone()[0],5)
    def test_fairness_denominators(self):
        s=pd.read_csv(ROOT/'outputs/fairness_slices.csv')
        self.assertTrue({'n','positives','false_positive_rate','regression_mae','small_group'}<=set(s.columns))
        clear=s.loc[s.group.eq('Clear')].iloc[0];self.assertEqual(clear.positives,0);self.assertTrue(pd.isna(clear.recall))
if __name__=='__main__':unittest.main()
