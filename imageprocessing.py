#import required image processing libraries


from matplotlib import pyplot as plt
import skimage
import os
from skimage import exposure
from skimage import segmentation
from skimage.feature import blob_dog, blob_log, blob_doh
from math import sqrt
from skimage.color import rgb2gray
import glob
from skimage.io import imread
from skimage.exposure import match_histograms
from skimage import filters
from skimage.util import crop
import numpy as np
from scipy import ndimage as ndi
from skimage import morphology
import cv2
from skimage.feature import canny
import pandas as pd

#import reference good image for images where the exposure was way too low (beginning on the 25 Oct)
refim=imread('../code/20191021_gl5_20.5m_delta495_8.tif',as_gray=True)


###functions###
def draw_group_as_background(ax, group, watershed_result, original_image):
#  Draws a group from the watershed result as red background."
    background_mask = (watershed_result == group)
    cleaned = original_image * ~background_mask
    ax.imshow(cleaned, cmap='gray')
    ax.imshow(background_mask,cmap='Reds')


###STRATEGY 1####

#how to import the image

print("Enter path of input files:")
path = input()

print("Enter main output path")
outpath = input()

print("Crop images? (Y/N)")
crop=input()

print("Axes? (Y/N)")
includeAxes=input()


if crop == 'Y':
    print("assuming 0,0 as left upper corner \n pixels y")
    ypix=input()
    print("pixels x")
    xpix=input()

pathlist=[]
countlist=[]
arealist=[]
namelist=[]

#for now, only define input path as one image folder. can't get it to work for nested folders within folders yet...
counts_frame=pd.DataFrame(columns=['image','count','totarea'])

for directory, subdir, file_list1 in os.walk(path):
    if len(subdir)!=0:  #if there are any subdirectories
        for sub in subdir:      #for each subdirectory in the list of subdirectories
            print('subdir',sub)

            for _, _, file_list2 in os.walk(directory+'/'+sub): #note, directory and subdirectories are not followed by a /
                for name in file_list2:
                    if name != '.DS_Store' and name != 'Thumbs.db':
                        print('filename',name)
                        pathlist.append(directory+'/'+sub+'/'+name)
#
    else:
        print('no sub')
        for name in file_list1:
            if name != '.DS_Store' and name != 'Thumbs.db':
                print(name)
                pathlist.append(directory+'/'+name)
#

pathlistfr=pd.DataFrame(pathlist,columns=['fname'])     #turn the list of pathnames into a dataframe

pathlistfr.drop(pathlistfr[pathlistfr.fname.str.contains('agg',case=False)].index,inplace=True)#drop any image names that contain dapi or aggregate

for name in pathlistfr.fname:
    print('name',name)
    outname=name[name.rfind('/')+1::]
    print('outname',outname)

    #read in file:

    im=imread(name,as_gray=True)
    
    if includeAxes=="N":
        plt.axis("off")

    im = match_histograms(im, refim)    #match histograms using good image bc some were way too dim exposure
   
    if includeAxes=="N":
        plt.axis("off")
        plt.imshow(im,cmap=plt.cm.gray) #cmap=plt.cm.gray
    
    else:
        plt.imshow(im)
        
    plt.savefig(outpath+'/'+outname+'histmatch.pdf',bbox_inches="tight")
    plt.close()

    im = filters.threshold_local(im, 15, method='gaussian', offset=0, mode='reflect', param=None, cval=0)
    if includeAxes=="N":
        plt.axis("off")
        plt.imshow(im,cmap=plt.cm.gray)
    else:
        plt.imshow(im)
        
    plt.savefig(outpath+'/'+outname+'dynthresh.pdf',bbox_inches="tight")
    plt.close()

#   Compute a threshold mask image based on local pixel neighborhood.
#
#   Also known as adaptive or dynamic thresholding. The threshold value is the weighted mean for the local neighborhood of a pixel
#   subtracted by a constant. Alternatively the threshold can be determined dynamically by a given function, using the ‘generic’ method.

#crop to desired area first y1:y2, x1:x2 (optional)
    if crop == 'Y':
        im = im[0:int(ypix), 0:int(xpix)]

    ####To detect the edges, we use the sobel filter####
    sobel = filters.sobel(im)

    plt.rcParams['image.interpolation'] = 'nearest'
    plt.rcParams['image.cmap'] = 'gray'
    plt.rcParams['figure.dpi'] = 200
    
    if includeAxes=="N":
        plt.axis("off")
    plt.imshow(sobel)
    plt.savefig(outpath+'/'+outname+'sobel.pdf',bbox_inches="tight")
    plt.close()


    ####blur image to thicken edges####
    blurred = filters.gaussian(sobel, sigma=2.0)
    if includeAxes=="N":
        plt.axis("off")
    plt.imshow(blurred)
    plt.savefig(outpath+'/'+outname+'blurred.pdf',bbox_inches="tight")
    plt.close()


    ####transform image into light zones and dark zones####


    #light
    light_spots = np.array((im > 0.15).nonzero()).T
    #light_spots.shape #print

    if includeAxes=="N":
        plt.axis("off")
    
    plt.plot(light_spots[:, 1], light_spots[:, 0], 'o',color="white")

    plt.imshow(im)
        
    plt.savefig(outpath+'/'+outname+'lightspots.pdf',bbox_inches="tight")
    plt.close()




     ####Masking####

     #Making a seed mask
    bool_mask = np.zeros(im.shape, dtype=np.bool)
    bool_mask[tuple(light_spots.T)] = True
    seed_mask, num_seeds = ndi.label(bool_mask)
    num_seeds

    #Applying the watershed
    ws = skimage.segmentation.watershed(blurred, seed_mask) #apportions pixels into marked basins  old: morphology.watershed(blurred, seed_mask)
    #(inputs-image, labels) and returns a matrix
    if includeAxes=="N":
        plt.axis("off")
    plt.imshow(ws)
    plt.savefig(outpath+'/'+outname+'watershed.pdf',bbox_inches="tight")
    plt.close()

    ####remove class with most pixels####
    background = max(set(ws.ravel()), key=lambda g: np.sum(ws == g)) #ravel wil take the watershed matrix and compress in to 1-D ndarray'; 'max will return the largest item in an iterable or the largest of two or more arguments. Key lambda applies np.sum to to each item. so in this case, i think it is finding where in ws the value from the 1D list of representative valus is, and finding the one that occurs the most frequently?

    ####make mask from background value
    background_mask = (ws == background)
    background_mask = ~background_mask # ~ is inverse

    #plt.imshow(background_mask)

    cleaned = im * background_mask
    #plt.imshow(cleaned)


    #check
    if includeAxes=="N":
        plt.axis("off")
    plt.imshow(background_mask,cmap=plt.cm.gray) #np.invert(background_mask)
    plt.savefig(outpath+'/'+outname+'background.pdf',bbox_inches="tight")
    plt.close()


    ###enumeration

    #blobs_log gives three outputs for each object found. First two are the coordinates and the third one is standard deviation of the Gaussian kernel that detected the blob. The radius of each blob is approximately 2*sigma for a 2D image


    #the image is blurred with increasing standard deviations and the difference between two successively blurred images are stacked up in a cube.  Blobs are again assumed to be bright on dark.

    #camera field area at 100 x:0.00595 mm^2; 14.84213851 pixels in 1 micrometer
    blobs_log=pd.DataFrame((blob_log(cleaned,max_sigma=30,num_sigma=10,threshold=0.1)),columns=['x','y','area'])

    blobs_log['radius']=blobs_log['area'].apply(lambda x:np.round(x*sqrt(2)/14.84,2))

    #filter out any "objects" with a radius of less than 0.1 micron (smaller than bacteria)

    #blobs_log.drop(blobs_log[blobs_log['radius'] < 0.10].index,inplace=True)

    numrows=blobs_log.shape[0] #number of cells
    totarea=np.sum(blobs_log.area) #total cell area

    countlist.append(numrows)
    arealist.append(totarea)
    namelist.append(outname)

    ### enumerate validation

    fig,ax=plt.subplots(1,1)
    if includeAxes=="N":
        plt.axis("off")
        
    plt.imshow(cleaned)

    for i in range (blobs_log.shape[0]):
        y,x,r=blobs_log['x'].iloc[i],blobs_log['y'].iloc[i],blobs_log['radius'].iloc[i]
        
        if includeAxes=="N":
            c=plt.Circle((x,y),r+5,color='white',linewidth=1,fill=False)
        else:
            c=plt.Circle((x,y),r+5,color='lime',linewidth=1,fill=False)
            
        ax.add_patch(c)

    fig.savefig(outpath+'/'+outname+'check.pdf',bbox_inches="tight")
    plt.close()


##after looping through all of the images, add the total/stats per image and the image name to the dataframe


counts_frame['image']=namelist
counts_frame['count']=countlist
counts_frame['totarea']=arealist

###output data to csv files. will have a separate program to merge all of the dataframes and sort by image
fileoutname=path[path.rfind('/')+1::]
counts_frame.to_csv(outpath+'/'+fileoutname+'.csv',index=False)
