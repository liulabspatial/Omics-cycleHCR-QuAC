# Protein and RNA cycleHCR with explainable ML <br/><br/>
img src="https://github.com/user-attachments/assets/ac239d2b-33c9-4d2e-9f95-a1e53a92ff3e"

Folders in this repository:<br/>
* Whole brain section image analysis pipeline:<br/>
i.   cycleHCR large image dataset processing pipeline and single-cell nuclear protein intensity and RNA expression measurements<br/>
ii.  UMAP construction and cell clustering using nuclear protein or RNA expression data<br/>
iii. Image classification of nuclear proteins from cell clusters generated based on nuclear protein intensities<br/>
iv.  Explainable machine learning using QuAC to discover cell-type specific nuclear structures<br/>
v.   Population-level quantitative validation on cell-type specific nuclear structural features identified using QuAC<br/>

* Cell culture image analysis pipeline:<br/>
vi.  Single-cell nuclear protein intensity measurement and cell-type classification using nuclear protein intensities<br/>
vii. Additional robustness analyses on Harmony and clustering<br/>
<br/><br/>

Links to additional repositories used in the pipeline:<br/>
Quantitative Attributions with Counterfactuals: [https://github.com/funkelab/quac/tree/main](https://github.com/funkelab/quac/tree/main)<br/>
cycleHCR image analysis pipeline: [https://github.com/liulabspatial/CycleHCR-Pipeline](https://github.com/liulabspatial/CycleHCR-Pipeline)


## Computational environments

This pipeline spans three coordinated environments matched to the
computational requirements of each stage. Each notebook header indicates
which environment it requires.

### 1. Image processing — Nextflow + Singularity (CycleHCR-Pipeline)

Image stitching, 3D registration, spot detection, and nuclear segmentation
are run as a Nextflow workflow with containerized processes executed
through SingularityCE. We used:

- SingularityCE v4.1.2
- Nextflow version 25.10.4.11173
- CycleHCR-Pipeline commit 8d3e1b6d097ba83af300cd4b095b2093011f78af

Setup instructions and the pipeline scripts (Step_1 through Step_5) are
in the CycleHCR-Pipeline repository:
https://github.com/liulabspatial/CycleHCR-Pipeline

The Singularity images used by the workflow are defined in the Nextflow
process modules and are pulled automatically on first run. Container
definitions are based on JaneliaSciComp/containers.

### 2. Analysis environment — Python (this repository, folders i–iii, v–vi)

Cell clustering, ML classification, and feature quantification.

    conda create -n omics-cyclehcr python=3.10
    conda activate omics-cyclehcr
    pip install -r requirements.txt

A version-locked `requirements.txt` is provided in the root of this
repository.

### 3. QuAC — Python + PyTorch/CUDA (folder iv)

Explainable-ML analysis with QuAC. Requires Linux x86_64 with CUDA 11.8.

    conda create -n quac python=3.10
    conda activate quac
    pip install "git+https://github.com/funkelab/quac.git@ce13955b9ad999c8b4673cbfb0b51bce72a551ea"

The upstream pyproject.toml pins torch==2.4.0 and other dependencies.
A CUDA 11.8-capable GPU is required for training and counterfactual
generation.
