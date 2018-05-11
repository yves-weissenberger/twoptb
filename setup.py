from setuptools import setup

setup(name='twoptb',
      version='0.1',
      description='toolbox for the analysis of two-photon imaging data',
      url='http://github.com/yves-weissenberger/twoptb',
      author='Yves Weissenberger',
      author_email='yvesweissenberger@gmail.com',
      license='MIT',
      scripts=['twoptb/scripts/convert_to_hdf5.py',
      		   'twoptb/scripts/motion_register_data.py',
      		   'twoptb/ROIs/ROI_Drawer.py',
      		   'twoptb/ROIs/run_roi_finder.py',
      		   'twoptb/ROIs/train_roi_finder.py',
      		   'twoptb/ROIs/share_roiinfo.py',
      		   'twoptb/ROIs/extract_roi_traces.py',
      		   'twoptb/across_days/aggregate_rois.py',
      		   'twoptb/across_days/across_day_traces.py',
      		   ],
      packages=['twoptb'],
      zip_safe=False)