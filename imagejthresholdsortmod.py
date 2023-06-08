#import required libraries


from matplotlib import pyplot as plt
import os
from os import listdir
from os.path import isfile, join
import numpy as np
import pandas as pd
import re

#list of poor quality images you want to exclude from the analysis
badList=pd.read_csv("/Volumes/Ashley's External Drive/Graduate Research/Gordon's Lab Data Backups/imagesonly/FISH/Eps682GL5nutrientenrichments/bad_images.csv")

print("Enter input path of csv image data:")
path = input()

print("Enter output path:")
outpath = input()

badList.filename=badList.filename.str[:-3]

onlyGoodIm = []
cellBgCorrFl=[]
stdevBgCorrFl=[]
noTrueCells=[]
noAllCells=[]
imArea=[]
StoBGtruecells=[]

bgAreaCorrFluor=[]


for f in listdir(path):
    if(isfile(join(path, f)) and f !='.DS_Store'): #DS store is mac specific
         print(f)
         
         if f[f.find('countsall')+len('countsall'):-3] not in list(badList.filename) and 'background' not in f:
            fr=pd.read_csv(join(path, f)) #if the image is not in the bad image file and it is not a background file
            
            dig = re.search(r"\d", f) #image number of discrete sample images
            
            if dig is not None:
                ind=dig.start()
                
                bgFileName="fluorbackground"+f[ind:]
                print("corresponding background file ",bgFileName)
                
                BGfr=pd.read_csv(join(path, bgFileName)) #pull corresponding background file
                print(BGfr)
                
                bgArea=BGfr['Area'][0]
                bgMeanGrey=BGfr['Mean'][0]
                bgIntDens=BGfr['IntDen'][0]

                
            else:
                print("No digit in that string")
            
            imName=f[f.find('countsall')+len('countsall'):-3]+'tif'
            print('Image name',imName) #derive image tif name from csv file
            
            
            print(len(fr['Area']),' entries')
            
            onlyGoodIm.append(imName) #append image name
            noAllCells.append(len(fr['Area'])) # total cells in entire image
            imArea.append(fr['im area um^2'][0]) #area of entire image
            
            bgAreaCorrFluor.append(bgIntDens/bgArea) #calculate the area corrected background fluorescence intensity
            
            fr['bg corr cell fluor int']=fr['IntDen']-(fr['Area']*bgMeanGrey) #calculate bg corrected integrated fl. int. for all cells
            fr['S/BG']=(fr['IntDen']/fr['Area'])/bgMeanGrey #uncorrected signal/area to bg/area
            
            
            #autofluorescence controls are indicated in filename by "auto". Fluorochrome is in the filename, that way can set threshold for each one.
            #pure culture controls, autofluorescence controls and DAPI images enter the "else" loop- nothing is dropped from these files.
            #keep autofluorescence controls in a separate directory- run first to establish the threshold values for if and elif loops.
            if 'CY3' in imName.upper() and 'AUTO' not in imName.upper() and 'ECOLI' not in imName.upper() and 'CONTROL' not in imName.upper():
                trueCells=fr[fr['bg corr cell fluor int']>45.6] #residual auto+2sigma
            
            elif 'CY5' in imName.upper() and 'AUTO' not in imName.upper() and 'ECOLI' not in imName.upper() and 'CONTROL' not in imName.upper():
                trueCells=fr[fr['bg corr cell fluor int']>5.19] #residual auto+2sigma old 4.67
            
            else:
                trueCells=fr
        
            noTrueCells.append(len(trueCells['Mean'])) # append number of real cells
            cellBgCorrFl.append(np.mean(trueCells['bg corr cell fluor int'])) #append average bg corrected cell fluor of true cells
            stdevBgCorrFl.append(np.std(trueCells['bg corr cell fluor int'])) #append stdev bg corrected cell fluor of true cells
            StoBGtruecells.append(np.mean(trueCells['S/BG']))
   
#after looping through all csv files, compile into one large df
outStatsall=pd.DataFrame({'Image Name':onlyGoodIm,'Total Cells':noAllCells,'True Cells':noTrueCells,'Image area (um^2)':imArea,'average true BAC-FI':cellBgCorrFl,'stdev true BAC-FI':stdevBgCorrFl,'bg area corrected fluor':bgAreaCorrFluor,'S/BG':StoBGtruecells})

#associate a discrete lab sample name with each file
outStatsall['labSamples']=outStatsall['Image Name'].apply(lambda x:x[x.find('_')+1:x.rfind('_')])

#sort the big data frames into small data frames by lab sample name and output
for s in np.unique(outStatsall['labSamples']):
    print(s)
    outFr=outStatsall[outStatsall['labSamples']==s]
    print(outFr)
    
    outFr.to_csv(outpath+"/"+s+".csv",index=False)
