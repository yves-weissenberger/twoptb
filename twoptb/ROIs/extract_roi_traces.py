#!/home/yves/anaconda2/bin/python



from __future__ import division
import h5py
import pickle
import copy as cp
import numpy as np
import sys
import os
import twoptb as MP
from oasis.functions import deconvolve


def extract_traces(areaFile,roiattrs):
        
    nROIs = len(roiattrs['idxs'])
    len_trace = areaFile.shape[0]


    roiattrs['traces'] = np.zeros([nROIs,len_trace])
    for idx in range(nROIs):
        sys.stdout.write('\r Extracting_Trace_from roi: %s' %idx)
        sys.stdout.flush()
        mpossx= roiattrs['idxs'][idx][0]
        mpossy = roiattrs['idxs'][idx][1]
        xLims = [np.min(mpossx)-10,np.max(mpossx)+10]
        yLims = [np.min(mpossy)-10,np.max(mpossy)+10]

        temp = areaFile[:,yLims[0]:yLims[1],xLims[0]:xLims[1]] *roiattrs['masks'][idx]
        temp = temp.astype('float64')
        temp[temp==0] = np.nan
        if np.all(areaFile[10:110,yLims[0]:yLims[1],xLims[0]:xLims[1]]>1000):
            roiattrs['traces'][idx] = np.nanmean(temp-1000,  axis=(1,2))
        else:
            roiattrs['traces'][idx] = np.nanmean(temp,  axis=(1,2))
    return roiattrs


       
def neuropil_correct(areaF,roi_attrs):
    


    nROIs = len(roiattrs['idxs'])
    len_trace = areaFile.shape[0]


    roiattrs['traces'] = np.zeros([nROIs,len_trace])
    roiattrs['neuropil_traces'] = np.zeros([nROIs,len_trace])
    roiattrs['corr_traces'] = np.zeros([nROIs,len_trace])
    for idx in range(nROIs):

        sys.stdout.write('\r Extracting_Trace_from roi: %s' %idx)
        sys.stdout.flush()

        mpossx= roi_attrs['idxs'][idx][0]
        mpossy = roi_attrs['idxs'][idx][1]
        xLims = [np.min(mpossx)-10,np.max(mpossx)+10]
        yLims = [np.min(mpossy)-10,np.max(mpossy)+10]
        temp = areaF[:,yLims[0]:yLims[1],xLims[0]:xLims[1]] *np.abs(roi_attrs['masks'][idx]-1)
        temp = temp.astype('float64')
        temp[temp==0] = np.nan

        if np.all(areaFile[10:110,yLims[0]:yLims[1],xLims[0]:xLims[1]]>1000):
            neuropil_trace = np.nanmean(temp-1000,axis=(1,2))
        else:
            neuropil_trace = np.nanmean(temp,axis=(1,2))



        temp = areaF[:,yLims[0]:yLims[1],xLims[0]:xLims[1]] *roi_attrs['masks'][idx]
        temp = temp.astype('float64')
        temp[temp==0] = np.nan

        if np.all(areaFile[10:110,yLims[0]:yLims[1],xLims[0]:xLims[1]]>1000):
            trace = np.nanmean(temp-1000,axis=(1,2))
        else:
            trace = np.nanmean(temp,axis=(1,2))

        
        corrected_trace = trace - .4*neuropil_trace

        roiattrs['traces'][idx] = trace
        roiattrs['neuropil_traces'][idx] = neuropil_trace
        roiattrs['corr_traces'][idx] = corrected_trace


    return roiattrs


def baseline_correct(roiattrs):
    import copy as cp
    """ Correct for drifting baseline"""
    nROIs = len(roiattrs['idxs'])
    cFrames = np.array(roiattrs['traces']).shape[1]

    roiattrs['dfF'] = np.zeros([nROIs,cFrames])
    roiattrs['raw_traces'] = cp.deepcopy(roiattrs['traces'])
    len_trace = len(roiattrs['traces'][0])

    st_window = 200#np.min([.2*len_trace,2000])
    for idx in range(nROIs):
        sys.stdout.write('\r Baseline Correcting ROI: %s' %idx)
        sys.stdout.flush()

        roiattrs['traces'][idx] = roiattrs['traces'][idx] - MP.process_data.runkalman(roiattrs['traces'][idx],50000,st_window)
        baseline = MP.process_data.runkalman(roiattrs['corr_traces'][idx],50000,st_window)
        roiattrs['corr_traces'][idx] = roiattrs['corr_traces'][idx] - baseline
        roiattrs['dfF'][idx] = roiattrs2['corr_traces'][idx]/baseline
        if 'neuropil_traces' in roiattrs.keys():
            roiattrs['neuropil_traces'][idx] -= MP.process_data.runkalman(roiattrs['neuropil_traces'][idx],50000,st_window)


    return roiattrs

def extract_spikes_alt(roiattrs):

    """ Infer approximate spike rates """
    print "\nrunning spike extraction"
    import c2s

    frameRate = 25
    if 'corr_traces' in roiattrs.keys():
        trace_type = 'corr_traces'
    else:
        trace_type = 'traces'
    data = [{'calcium':np.array([i]),'fps': frameRate} for i in roiattrs[trace_type]]
    spkt = c2s.predict(c2s.preprocess(data),verbosity=0)

    nROIs = len(roiattrs['idxs'])
    cFrames = np.array(roiattrs['traces']).shape[1]

    spk_traces = np.zeros([nROIs,cFrames])
    spk_long = []
    for i in range(nROIs):
        spk_traces[i] = np.mean(spkt[i]['predictions'].reshape(-1,4),axis=1)
        spk_long.append(spkt[i]['predictions'])

    roiattrs['spike_inf'] = spk_traces
    roiattrs['spike_long'] = np.squeeze(np.array(spk_long))
    return roiattrs



def extract_spikes(roiattrs):


    frameRate = 25
    if 'corr_traces' in roiattrs.keys():
        trace_type = 'corr_traces'
    else:
        trace_type = 'traces'
    nROIs = len(roiattrs['idxs'])
    spk_traces = []
    print(np.isfinite(roiattrs['corr_traces']).all())
    print((roiattrs['corr_traces']).shape)

    for tr in roiattrs['corr_traces']:
        if np.all(np.isfinite(tr)):
            spk_traces.append(deconvolve(tr)[1])
        else:
            print('setting nan')
            spk_traces.append([np.nan]*len(tr))

    roiattrs['spike_inf'] = np.array(spk_traces)
    roiattrs['spike_long'] = np.nan
    return roiattrs


if __name__=='__main__':
    
    hdf_path = os.path.abspath(sys.argv[1])
    npc = sys.argv[2]=='y'
    kf = sys.argv[3]=='y'
    spks = sys.argv[4]=='y'
    print "neuropil correct: %s" %npc
    print "kalman filter: %s" %kf
    print "kalman filter: %s" %extract_spikes

    #roi_pth = os.path.join(hdf_path[:-3],'ROIs')
    with h5py.File(hdf_path,'a',libver='latest') as hdf:
        keys = hdf.keys()
        Folder = os.path.split(os.path.abspath(hdf.filename))[0]
        roi_pth = os.path.join(Folder,'ROIs')
        print '\n\n'
        f = hdf[keys[0]]['registered_data']


        sessions = list((i for i in f.iterkeys()))
        n_sess = len(sessions)
        for idx,fn in enumerate(sessions):

            print '\narea %s/%s: %s' %((idx+1),n_sess,fn)

            areaFile = f[fn]
            if 'ROI_dataLoc' in areaFile.attrs.keys():
                FLOC = areaFile.attrs['ROI_dataLoc']
            else:
                Folder = os.path.split(os.path.abspath(areaFile.file.filename))[0]
                fName = areaFile.name[1:].replace('/','-') + '_ROIs.p'
                FLOC = os.path.join(Folder,'ROIs',fName)
                areaFile.attrs['ROI_dataLoc'] = FLOC

            roiattrs = pickle.load(open(FLOC,'r'))
            if npc:
                roiattrs2 = neuropil_correct(areaFile,roiattrs)
            else:
                roiattrs2 = roiattrs
                roiattrs2['corr_traces'] = roiattrs['traces']
            print "\n"
            if kf:
                roiattrs2 = baseline_correct(roiattrs2)
            if spks:
                try:
                    import c2s
                    roiattrs2 = extract_spikes(roiattrs2)

                except ImportError:
                    print "WARNING COULD NOT INFER SPIKE RATES AS c2s HAS NOT BEEN INSTALLED"
            with open(FLOC,'wb') as fi:
                pickle.dump(roiattrs2,fi)



    print 'done!'
                

