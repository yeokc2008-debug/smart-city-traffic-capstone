"""Tree SHAP explains a comparable demand regressor, not the neural weights."""
import logging,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import shap
from sklearn.metrics import r2_score,mean_absolute_error
from config import ROOT,SEED
logger=logging.getLogger(__name__)

def explain_demand(df,x,models):
    test=df.split.eq('test');indices=df.loc[test].sample(n=min(150,int(test.sum())),random_state=SEED).index
    forest=models['forest_reg_v2'];z=forest.named_steps['standardscaler'].transform(x.loc[indices])
    explainer=shap.TreeExplainer(forest.named_steps['randomforestregressor'])
    values=explainer.shap_values(z,check_additivity=True)
    importance=pd.DataFrame({'feature':x.columns,'mean_absolute_shap_vehicles':np.abs(values).mean(axis=0)}).sort_values('mean_absolute_shap_vehicles',ascending=False)
    importance.to_csv(ROOT/'outputs/shap_importance.csv',index=False)
    pd.DataFrame(values,columns=x.columns,index=indices).to_csv(ROOT/'outputs/shap_values_sample.csv')
    shap.summary_plot(values,z,feature_names=list(x.columns),show=False,max_display=12,plot_size=(9,5.5))
    plt.tight_layout();plt.savefig(ROOT/'outputs/figures/06_shap_demand.png',dpi=140,bbox_inches='tight');plt.close()
    neural=models['neural_v3'].predict(x.loc[test]);rf=forest.predict(x.loc[test])
    comparison={'explained_model':'forest_reg_v2','deep_model':'neural_v3',
                'test_agreement_r2_neural_as_reference':r2_score(neural,rf),
                'mean_absolute_prediction_disagreement':mean_absolute_error(neural,rf),
                'shap_sample_hours':len(indices),
                'scope':'Comparable model for same demand task and features, not direct neural explanation or causal attribution.'}
    (ROOT/'outputs/explanation_scope.json').write_text(json.dumps(comparison,indent=2))
    logger.info('Tree SHAP saved for %d test observations; RF/neural MAE disagreement %.2f',len(indices),comparison['mean_absolute_prediction_disagreement'])
    return importance
