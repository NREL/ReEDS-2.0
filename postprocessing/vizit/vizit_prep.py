import os
import shutil
import sys
import pandas as pd
import requests

vizit_commit = '205521ad93c70f3212f724fac9db6c69d12ec098'
thisDir = os.path.dirname(os.path.realpath(__file__))
outputDir = sys.argv[1]
bpStyleDir = (os.path.join(thisDir,os.pardir,'bokehpivot','in','reeds2'))

ls_df = []
#Read in styles from bokehpivot
for f in os.listdir(bpStyleDir):
    if f.endswith('_style.csv'):
        df = pd.read_csv(os.path.join(bpStyleDir,f))
        df['column_name'] = f.replace('_style.csv','')
        df = df.rename(columns={'order':'column_value'})
        ls_df.append(df)

df_style = pd.concat(ls_df,ignore_index=True)
df_style = df_style[['column_name','column_value','color']].copy()

#Get specified version of vizit based on commit hash
vizit_filename = 'vizit-open this and point to all files in csvs dir.html'
vizit_url = f'https://raw.githubusercontent.com/mmowers/vizit/{vizit_commit}/index.html'
vizit_html = requests.get(vizit_url).text
if vizit_html == '404: Not Found':
    vizit_html = (f'<!DOCTYPE html>\nCould not retrieve <a href="{vizit_url}">{vizit_url}</a>.<br><br>'
                  'Save that link as an html file, or go to latest vizit at '
                  '<a href="https://mmowers.github.io/vizit/">https://mmowers.github.io/vizit/</a>')

#Dump vizit files into standard reduced report
with open(os.path.join(outputDir, 'reeds-report-reduced', vizit_filename), 'w') as f:
    f.write(vizit_html)
shutil.copy2(os.path.join(thisDir, 'standard_reduced_report.json'),
             os.path.join(outputDir,'reeds-report-reduced','csvs'))
df_style.to_csv(os.path.join(outputDir,'reeds-report-reduced','csvs','style.csv'), index=False)

#Dump vizit files into state report
with open(os.path.join(outputDir, 'reeds-report-state', vizit_filename), 'w') as f:
    f.write(vizit_html)
shutil.copy2(os.path.join(thisDir, 'state_report.json'),
             os.path.join(outputDir,'reeds-report-state','csvs'))
df_style.to_csv(os.path.join(outputDir,'reeds-report-state','csvs','style.csv'), index=False)