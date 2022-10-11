# update user cases to include all options in A_Inputs/cases.csv
#%%
import os
import pandas as pd

#%%
casesdir = os.path.join("..", "..", "A_Inputs", "cases.csv")
cases = pd.read_csv(casesdir)

users = [x for x in os.listdir() if not x.endswith(".py")]

for user in users:
    usercases = os.path.join(user, "cases.csv")
    if os.path.exists(usercases):
        csv = pd.read_csv(usercases)
        userops = csv['case']
        add = cases.loc[~cases['case'].isin(userops)]
        update = pd.concat([csv, add])
        update.sort_index(inplace=True)
        update.to_csv(usercases, index=False)

# %%
