:: To launch the bokehpivot interface, you'll need the "reeds" conda environment from here: 
:: https://github.nrel.gov/ReEDS/ReEDS-2.0/blob/b00b07440984ecfb06b2eae33766598a78bd6830/environment.yml
:: For more details on the issue with "reeds2", see https://github.nrel.gov/ReEDS/ReEDS-2.0/issues/1146.
call conda activate reeds
bokeh serve . --sh --port 0
cmd /k