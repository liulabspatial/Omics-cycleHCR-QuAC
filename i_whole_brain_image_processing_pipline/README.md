Step 1 image stitching, <br/>
Step 2 cross-cycle image registration (customized code in /scripts/ folder), <br/>
Step 3 RNA spot calling, <br/>
and Step 5 RNA spot-to-cell assignment <br/>
are performed using cycleHCR image processing pipeline published in another repository [https://github.com/liulabspatial/CycleHCR-Pipeline](https://github.com/liulabspatial/CycleHCR-Pipeline).<br/>

The shell codes for processing the specific image datasets of the mouse whole-brain sections are provided here. <br/> <br/>

Dockers for  <br/>
Step 4 nuclei segmentation using distributed Cellpose, <br/>
Step 6 3D single-nucleus image extraction, <br/>
Step 7 measure single-nucleus protein intensity, <br/>
and Step 12 write ML training and validation image datasets (need pre-assigned cell ID list from Step 11) <br/> <br/>

are provided.
