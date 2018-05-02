import numpy as np
import matplotlib.pyplot as plt
import twoptb
import time
from skimage import morphology
import h5py
from IPython import display
import os
import pickle
import sys
from skimage.exposure import equalize_adapthist
from sklearn.ensemble import RandomForestClassifier
import re



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
            if os.path.split(os.path.split(roip)[0])[0]==os.path.split(hdfp)[0]:
                pairs.append([roip,hdfp])
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
            tar_area = re.findall(r'.*(\(2018.*)_ROIs.p',os.path.split(pair[0])[1])[0]
            mnIm = bhdf1[tar_area].attrs['mean_image']
        
        mnIm = equalize_adapthist(mnIm/np.max(mnIm),clip_limit=0.005)
        roi_mIm_sets.append([mnIm,roiB])
    return roi_mIm_sets


def get_training_sets(roi_mIm_sets,rad=7):
    
    

    boutons = []

    non_boutons = []
    for mIm,roiB in roi_mIm_sets:
        for c in roiB['centres']:
            xc = int(np.round(c[0]))
            yc = int(np.round(c[1]))
            t_ = (mIm[yc-rad:yc+rad,xc-rad:xc+rad]).flatten()
            if np.max(t_)==0:
                pass
            else:
                boutons.append(np.concatenate([t_/np.max(t_),[np.mean(t_)]]))

            RN = np.random.randint(0,10)
            if RN<2:
                xcR,ycR = np.array([xc,yc]) + np.array([np.random.randint(3,7),np.random.randint(3,7)])
                tR_ = (mIm[ycR-rad:ycR+rad,xcR-rad:xcR+rad]).flatten()

                if np.max(tR_)==0:
                    pass
                else:
                    non_boutons.append(np.concatenate([tR_/np.max(tR_),[np.mean(tR_)]]))
            elif RN in range(4,5):
                xcR,ycR = (np.random.randint(50,450),np.random.randint(10,500))
                tR_ = (mIm[ycR-rad:ycR+rad,xcR-rad:xcR+rad]).flatten()

                if np.max(tR_)==0:
                    pass
                else:
                    non_boutons.append(np.concatenate([tR_/np.max(tR_),[np.mean(tR_)]]))


    boutons = np.array(boutons)
    non_boutons = np.array(non_boutons)
    return boutons,non_boutons

if __name__=="__main__":

    if len(sys.argv)<2:
        print "Missing required arguments: first argument is radius to draw patches"
        raise
    rad = int(sys.argv[1])
    classifier_name = sys.argv[2]
    paths = sys.argv[3:]


    #Load and setup data to train classifier with
    pairs = get_roi_paths(['/media/yves/imaging_yves/Trudy/20180429/','/media/yves/imaging_yves/Betty/20180429/'])

    sets = get_mean_im_roi_centroids(pairs)
    boutons,non_boutons = get_training_sets(sets,rad)

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


