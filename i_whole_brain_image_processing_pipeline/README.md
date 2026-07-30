Step 1 image stitching, <br/>
Step 2 cross-cycle image registration (customized code in /scripts/ folder), <br/>
Step 3 RNA spot calling, <br/>
and Step 5 RNA spot-to-cell assignment <br/>
are performed using cycleHCR image-processing pipeline published in another repository [https://github.com/liulabspatial/CycleHCR-Pipeline](https://github.com/liulabspatial/CycleHCR-Pipeline).<br/> 

Shell scripts for processing the specific mouse whole-brain image datasets are provided. <br/> <br/>

Dockers are provided for  <br/>
Step 4 nuclei segmentation using distributed Cellpose, <br/>
and Step 6 3D single-nucleus image extraction <br/> <br/>

Step 7 single-nucleus protein intensity quantification, <br/>
and Step 12 generation of ML training and validation image datasets (need a pre-assigned cell ID list from Step 11) <br/>
run as standalone python scripts with the packages in requirements.txt (no Docker needed). <br/>
Edit the USER CONFIG block at the top of each script, then run: <br/>

```
python Step_7_measure_nucleus_intensity.py
python Step_12_1_write_ML_image_dataset.py
```
 
