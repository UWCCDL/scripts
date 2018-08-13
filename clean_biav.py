import pandas as pd

### CHANGE HERE ###
data_file = "" 
change_length = 1  
fs = 100
Triggers = []
output_file = ""


### SCRIPTS ###
df = pd.read_csv(data_file)
length = change_length * fs
for trigger in Triggers:
    trigger_starts = df[df.Trigger == trigger].index
    for idx in trigger_starts:
        df.loc[idx : idx + length, "Trigger"] = trigger

df.to_csv(output_file, index=None)

