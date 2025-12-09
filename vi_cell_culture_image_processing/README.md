This folder contains a pipeline for processing cell culture images to cluster cells using nuclear protein intensity.
Clustering results are compared to ground-truth cell-type identification based on fluorescence intensity of cell type markers.


The pipeline is suitable for cell culture image datasets with these features:
* Image datasets contain individual fields of view and thus do not require image stitching.
* Smaller dataset sizes (e.g., 41 fields of view) potentially allow several steps (e.g., registration) to run on local computers instead of high-density clusters.
* Cell types defined by protein markers (no RNA data).

