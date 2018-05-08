import numpy as np
import matplotlib.pyplot as plt
import time
from skimage import morphology
import h5py
from IPython import display
import os
import pickle
import skimage
import sys
from skimage.exposure import equalize_adapthist
from sklearn.ensemble import RandomForestClassifier
import re


""" 
Train a classifier to find the centroids of ROIs based on mean images

Arguments:
===================================


    rad:    int
    
            integer specifying (in pixels) the radius of the 
            patch used to train the classifier

    name:   str

            name of the classifier (as it is to be saved in 
            /path/to/twoptb/classifiers/)

    paths:  str(s)

            path to directories containing hdf5 files with ROIs drawn
            directories. If directory contains multiple hdf-files they
            will be recursively discovered.


 """


def findpath():
    cDir = os.path.dirname(os.path.realpath(__file__))

    found = False
    while not found:
        cDir,ext = os.path.split(cDir) 
        if ext=='twoptb':
            found = False
            twoptb_path = cDir
            print 
            break
    return twoptb_path

twoptb_path = findpath()
sys.path.append(twoptb_path)
#sys.path.append(os.path.abspath())
import twoptb as MP


def get_roi_paths(in_args):

    """ Returns list of all hdf paths"""
    roiPaths = []
    hdfPaths = []
    n_basedirs = len(in_args)
    for dir_ix in range(n_basedirs):
        base_dir = in_args[dir_ix]
        for root, dirs, files in os.walk(base_dir):
            for fl in files:
                if fl.endswith("ROIs.p"):
                    # print(os.path.join(root, fl)) 
                    roiPaths.append(os.path.join(root,fl))
                if fl.endswith(".h5"):
                    # print(os.path.join(root, fl)) 
                    hdfPaths.append(os.path.join(root,fl))

                    
    
    pairs = []
    for roip in roiPaths:
        
        for hdfp in hdfPaths:
            if ('_1_' in roip) or ('_2_' in roip) or ('_3_' in roip):
                pass
            else:
                if os.path.split(os.path.split(roip)[0])[0]==os.path.split(hdfp)[0]:
                    pairs.append([roip,hdfp])


    cleaned_pairs = []
    completed_hdfPaths= []

    for i,j in pairs:
        if j not in completed_hdfPaths:
            with h5py.File(j) as hdfF1:
                bhdf1 =  hdfF1[hdfF1.keys()[0]][ u'registered_data']
                areas = bhdf1.keys()
                com_ref = bhdf1[areas[0]].attrs['common_ref']
                if com_ref:
                    completed_hdfPaths.append(j)
            cleaned_pairs.append([i,j])
                

    for i,j in cleaned_pairs:
        print i,j
        print ''

    return pairs



def get_mean_im_roi_centroids(pairs):


    roi_mIm_sets = []
    for pair in pairs:

        with h5py.File(pair[1]) as hdfF1:
            bhdf1 =  hdfF1[hdfF1.keys()[0]][ u'registered_data']
            areas = bhdf1.keys()
            #print pair[0],areas
            #print '\n..'
            roiB = pickle.load(open(pair[0]))
            tar_area = re.findall(r'.*(\(201.*)_ROIs.p',os.path.split(pair[0])[1])[0]
            mnIm = bhdf1[tar_area].attrs['mean_image']
        
        mnIm = equalize_adapthist(mnIm/np.max(mnIm),clip_limit=0.005)
        roi_mIm_sets.append([mnIm,roiB])
    return roi_mIm_sets


def get_training_sets(roi_mIm_sets,rad=7):
    
    

    boutons = []

    non_boutons = []
    print 'one'
    rIMS = []
    for mIm,roiB in roi_mIm_sets:
        for c in roiB['centres']:
            xc = int(np.round(c[0]))
            yc = int(np.round(c[1]))
            if np.logical_or.reduce((xc>(510-rad),yc>(510-rad),xc<(5+rad),yc<(5+rad))):
                pass
            else:
                rIMS.append((mIm[yc-rad:yc+rad,xc-rad:xc+rad]))
                t_ = (mIm[yc-rad:yc+rad,xc-rad:xc+rad]).flatten()
                if np.max(t_)==0:
                    pass
                else:
                    boutons.append(np.concatenate([t_/np.max(t_),[np.mean(t_)]]))

                RN = np.random.randint(0,10)
                if RN<2:

                    #xcR,ycR = np.array([xc,yc]) + np.array([np.random.randint(6,14),np.random.randint(6,14)]) #for zoom 2
                    xcR,ycR = np.array([xc,yc]) + np.array([np.random.randint(3,7),np.random.randint(3,7)]) #for zoom 1
                    tR_ = (mIm[ycR-rad:ycR+rad,xcR-rad:xcR+rad]).flatten()

                    if np.logical_or.reduce([np.max(tR_)==0,xcR<(rad+5),ycR<(rad+5),xcR>(510-rad),ycR>(510-rad)]):
                        pass
                    else:
                        non_boutons.append(np.concatenate([tR_/np.max(tR_),[np.mean(tR_)]]))
                elif RN in range(4,5):
                    xcR,ycR = np.clip((np.random.randint(50,450),np.random.randint(5+rad,510-rad)),rad,510-rad)
                    tR_ = (mIm[ycR-rad:ycR+rad,xcR-rad:xcR+rad]).flatten()

                    if np.logical_or.reduce([np.max(tR_)==0,xcR<(rad+5),ycR<(rad+5),xcR>(510-rad),ycR>(510-rad)]):
                        pass
                    else:
                        non_boutons.append(np.concatenate([tR_/np.max(tR_),[np.mean(tR_)]]))


    boutons = np.array(boutons)
    non_boutons = np.array(non_boutons)
    print 'here'
    plt.imshow(np.mean(np.array(rIMS),axis=0),cmap='binary_r')
    plt.show()
    return boutons,np.array(non_boutons)

if __name__=="__main__":

    if len(sys.argv)<2:
        print "Missing required arguments: first argument is radius to draw patches"
        raise
    rad = int(sys.argv[1])
    classifier_name = sys.argv[2]
    paths = sys.argv[3:]


    #Load and setup data to train classifier with
    pairs = get_roi_paths(paths)

    sets = get_mean_im_roi_centroids(pairs)
    boutons,non_boutons = get_training_sets(sets,rad)
    #print type(boutons), type(non_boutons)
    #print boutons.shape, non_boutons.shape
    train_set = np.vstack([np.array(boutons),np.array(non_boutons)])
    labels = np.concatenate([np.ones(boutons.shape[0]),np.zeros(non_boutons.shape[0])])

    rfClass = RandomForestClassifier(n_estimators=25,n_jobs=10,min_samples_split=5,min_samples_leaf=5) #good version
    #rfClass = RandomForestClassifier(n_estimators=25,n_jobs=10,min_samples_split=15,min_samples_leaf=15) #good version
    rfC_fit = rfClass.fit(np.vstack([np.array(boutons),np.array(non_boutons)]),labels)
    twoptb_path = findpath()
    classifier_path = os.path.join(twoptb_path,'twoptb','classifiers')

    if not os.path.isdir(classifier_path):
        os.mkdir(classifier_path)

    pickle.dump([rfC_fit,rad],open(os.path.join(classifier_path,classifier_name+'.p'),'wb'))


