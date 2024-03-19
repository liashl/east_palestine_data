import pandas as pd
from itertools import islice

df = pd.read_csv('norfolk_southern_data_3.csv')

print(df.head(10))
print(df.shape)
print(df.columns)

count = 0

#generate dictionary with chemicals as keys
#values is a list of samples they were found in



#find unique chemicals that are detected in the dataframe
unique_chems = []

for index, row in df.iterrows():
    if df['result'][index] != 'ND':
        chemical = df['analyte'][index]
        if chemical not in unique_chems:
            unique_chems.append(chemical)

#print(unique_chems)

#initialize dictionary
chem_dict = {x:[] for x in unique_chems}

#print(chem_dict)

for index,row in df.iterrows():
    if df['result'][index] != 'ND':
        chem_dict[df['analyte'][index]].append((df['client_sample_id'][index],df['result'][index],df['unit'][index],df['dil fac'][index],df['matrix'][index]))





#count detects for each analyte

chem_counts = {}
for key in chem_dict:
    chem_counts[key] = len(chem_dict[key])

#order dictionary by the number of detections
chem_count_sorted = {k: v for k, v in sorted(chem_counts.items(), key=lambda item: item[1], reverse=True)}

print(chem_count_sorted)

for chem in islice(chem_count_sorted, 13):
    print(chem)
    
    detections_df = pd.DataFrame(chem_dict[chem], columns=['client_sample_id','result','unit','dil_fac','matrix'])
    print(detections_df.head(20))

    print('###')