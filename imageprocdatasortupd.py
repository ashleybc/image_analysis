#import required libraries


from matplotlib import pyplot as plt
import os
from math import sqrt
import numpy as np
from scipy import ndimage as ndi
import pandas as pd


print("Enter input path:")
path = input()

print("Enter main output path")
outpath = input()

frames=[]


for directory, subdir, file_list1 in os.walk(path):
    for name in file_list1: #locate the csv files
        if '.csv' in name:
            print(name)
            fr=pd.read_csv(directory+'/'+name)
            frames.append(fr)

#merge into one large data frame
merged=pd.concat(frames, axis=0, join='outer', ignore_index=True,copy=True)
merged['sampleid'] = merged.image.apply(lambda x: x[x.find('_')+1:x.rfind('_')])

#make list of unique sample IDs in merged dataframe
samplenames=merged.sampleid.unique()
print("unique ids",samplenames)

##from here, the goal was to sort into dataframe by sample ID and re-output
for name in samplenames:
    nbool=merged.sampleid.str.contains(name,regex=False)
    nfr=merged[nbool]
    print("frame",nfr)
    nfr.to_csv(outpath+'/'+name+'.csv',index=False)





