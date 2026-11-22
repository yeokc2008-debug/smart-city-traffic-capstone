"""Fixed-threshold drift diagnostics; stress scenarios are explicitly synthetic."""
import logging,json
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from config import ROOT
logger=logging.getLogger(__name__)

def psi(reference,current):
    bins=np.unique(np.quantile(reference,np.linspace(0,1,11)))
    if len(bins)<3:return 0.0
    bins[0]=-np.inf;bins[-1]=np.inf
    a=np.histogram(reference,bins=bins)[0]+.5;b=np.histogram(current,bins=bins)[0]+.5
    a=a/a.sum();b=b/b.sum()
    return float(np.sum((b-a)*np.log(b/a)))

def assess(reference,current,reference_mae,current_mae):
    psis={col:psi(reference[col],current[col]) for col in ['temp_c','clouds_all','hour']}
    reasons=[f'{key} PSI={value:.3f} exceeds 0.20' for key,value in psis.items() if value>.20]
    if current_mae>reference_mae*1.25:reasons.append('MAE exceeds 1.25 times validation reference')
    status='ALERT' if reasons else 'PASS'
    if reasons:logger.warning('Monitoring ALERT: %s','; '.join(reasons))
    else:logger.info('Monitoring PASS: thresholds not exceeded')
    return {'status':status,'psi':psis,'reference_mae':float(reference_mae),'current_mae':float(current_mae),'reasons':reasons}

def simulate_monitoring(df,x,models,selection):
    valid=df.split.eq('validation');test=df.split.eq('test');reg=models[selection['regression']]
    ref=x.loc[valid];live=x.loc[test]
    reference_mae=mean_absolute_error(df.loc[valid,'traffic_volume'],reg.predict(ref).clip(0))
    prediction=reg.predict(live).clip(0);mae=mean_absolute_error(df.loc[test,'traffic_volume'],prediction)
    baseline=assess(ref,ref,reference_mae,reference_mae)
    normal=assess(ref,live,reference_mae,mae)
    stress=live.copy();stress['temp_c']+=15
    # A deliberate prediction offset represents an injected error stress, not observed labels.
    stress_error=mean_absolute_error(df.loc[test,'traffic_volume'],prediction+2000)
    injected=assess(ref,stress,reference_mae,stress_error)
    result={'thresholds':{'feature_psi':.20,'error_mae_ratio':1.25},
        'baseline_self_comparison':baseline,'observed_2018_test':normal,'synthetic_stress':injected,
        'stress_definition':'Add 15 Celsius to feature values and 2000 vehicles/hour to predictions; synthetic diagnostics, not observed production.',
        'interpretation':'Heuristic thresholds fixed before monitoring. Seasonal coverage differences can trigger feature drift; labels are needed for delayed error monitoring. PASS does not certify safety.'}
    assert baseline['status']=='PASS' and injected['status']=='ALERT'
    (ROOT/'outputs/monitoring.json').write_text(json.dumps(result,indent=2))
    (ROOT/'outputs/monitoring_dashboard.html').write_text('<!doctype html><meta charset="utf-8"><title>Traffic monitoring simulation</title><h1>Traffic monitoring simulation</h1>'+''.join(f'<h2>{name}: {value["status"]}</h2><p>{"; ".join(value["reasons"]) or "No configured threshold exceeded"}</p>' for name,value in [('Baseline self check',baseline),('Observed 2018',normal),('Synthetic stress',injected)])+'<p>Synthetic stress is deliberately injected. PASS does not certify safety.</p>')
    return result
