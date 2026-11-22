import subprocess,sys
steps=[['part2_python/pipeline.py','--input','data/Metro_Interstate_Traffic_Volume.csv'],['part1_data_analytics/analyse.py'],['part3_machine_learning/train_models.py'],['part3_machine_learning/unsupervised.py'],['part3_machine_learning/lime_explain.py'],['part3_machine_learning/advanced_ai.py'],['part3_machine_learning/monitor.py']]
for s in steps: subprocess.run([sys.executable,*s],check=True)
