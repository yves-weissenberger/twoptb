#A toolbox (under development) for processing two-photon imaging data in python2.7

More complete documentation can (soon) be found <a href="https://yves-weissenberger.github.io/twoptb/">here </a>


<h2> Includes complete pre-processing pipeline image registration GUIs for ROI extraction and mask drawing</h2>


<h3>Dependencies</h3>

<li>numpy</li>
<li>scipy</li>
<li>scikit-image</li>
* tifffile
* pyqt
* pyqtgraph (optional)



# How to run 

## 1. Convert Raw Data to HDF5 

    run convert_to_hdf5.py

    Converts all data from .tif and .mat to hdf5 format for further processing. See script 
    for details of required directory structure.

## 2. Motion Register Data

    run motion_register_data.py
    
    Motion registration is based on the efficient subpixel registration routine. The reference image is automatically
    selected by generating 100 (?) reference images based on random frames and selecting the sharpest (proxy for sharp-
    ness here is np.sum(np.abs(np.grad(reference_image)),axis=(0,1))

## 3. Drawing ROIs

### 3.1. PyQtGraph_ROI_Drawer.py
    This is a GUI that enables manual drawing of ROIs

    Using this ROI drawer, ROIs are drawn on individual sessions that are grouped together in the hdf5 file.
    If multiple sessions share a common reference, the ROIs are typically be shared across acquisition runs
    to do this run 

    twoptb/ROIs/share_roiinfo.py /path/to/my_hdf5.py

    and the ROIs will be copied across acquitions. Importantly, only one session can serve as a seed to copy from,
    all other WILL BE OVERWRITTEN. 

### 3.2. run_roi_finder.py
    After having drawn ROIs on 'training' datasets, this automatic roi-drawing tool may be used by initially 
    training an ROI drawer using train_roi_finder.py
    

    Using this ROI drawer, ROIs are drawn on individual sessions that are grouped together in the hdf5 file.
    If multiple sessions share a common reference, the ROIs are typically be shared across acquisition runs
    to do this run 

    python twoptb/ROIs/share_roiinfo.py /path/to/my_hdf5.py

    and the ROIs will be copied across acquitions. Importantly, only one session can serve as a seed to copy from,
    all other WILL BE OVERWRITTEN. 


## 4. Extract ROI Traces

    In this part of the pipeline we will extract traces, run neuropil correction, spike inference (c2s) etc
    To run this, simply run

    python twoptb/ROIs/extract_roi_traces.py /path/to/my_hdf5.py