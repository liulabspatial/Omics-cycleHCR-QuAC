# Reproducing the analyses

This document is the step-by-step recipe for re-running every key analysis in
the paper from a fresh clone of this repository. For the *installation* side
of reproduction (which conda environments to create, pinned package versions),
see the **"Computational environments"** section of `README.md`. This file
describes only **what to run, in what order, with which inputs, to produce
which outputs**.

---

## 0. Where to get the data

All input datasets are hosted on Zenodo:

> **Zenodo record:** 10.5281/zenodo.18633455

Each downstream folder has its own short `README.md` describing exactly which
file to download from Zenodo and where to put it. In every case the procedure
is the same:

```bash
# Inside the folder that needs data (e.g. ii_whole_brain_cell_clustering/),
# download input.zip from the Zenodo record, then:
unzip input.zip
# The unzipped input/ folder must sit directly under the section folder.
```

The QuAC raw image dataset on Zenodo (per-cell 3D nuclear crops, produced by
section `i` from the raw cycleHCR volumes) is shared across sections `iii`,
`iv`, and `v`.

---

## 1. Pipeline overview

```
                 RAW DATA (off-Zenodo: cycleHCR microscopy volumes)
                         │
                         ▼
   ┌────────────────────────────────────────────────────────────────┐
   │  i. Whole-brain image processing                               │
   │     Nextflow + Singularity (CycleHCR-Pipeline) and Docker      │
   │     Step_1 … Step_7  -> per-cell tables + per-cell 3D crops    │
   └────────────────────────────────────────────────────────────────┘
                         │ Zenodo deposits (input.zip + QuAC raw images)
                         ▼
   ┌────────────────────────────────────────────────────────────────┐
   │  ii. Whole-brain cell clustering   (analysis env)              │
   │     Steps 8_1 … 11   nuclear-protein + RNA UMAP, clusters      │
   └────────────────────────────────────────────────────────────────┘
              │                              │
              │ adata snapshots              │ cluster cell-ID lists
              ▼                              ▼
   ┌────────────────────┐         ┌───────────────────────────────┐
   │  iii. ML class.    │         │  vii. Robustness tests        │
   │  (analysis env,    │         │  (analysis env)               │
   │   GPU recommended) │         │  Harmony / PCA / clustering   │
   │  QuAC raw images   │         │  / random-seed sensitivity    │
   │  (Zenodo)          │         └───────────────────────────────┘
   └────────────────────┘
              │                  ┌────────────────────────────────┐
              ▼                  │ iv. QuAC explainable ML        │
   (same QuAC raw images on ────►│   (QuAC env, CUDA 11.8, GPU)   │
    Zenodo feed iii / iv / v)    │   funkelab/quac + YAML config  │
              ▲                  └────────────────────────────────┘
              │                  ┌────────────────────────────────┐
              └─────────────────►│ v. QuAC feature quantitation   │
                                 │   (analysis env)               │
                                 │   Population-level validation  │
                                 └────────────────────────────────┘

   ┌────────────────────────────────────────────────────────────────┐
   │  vi. Cell-culture pipeline   (analysis env, independent)       │
   │     Raw cell-culture stacks acquired by the authors; not       │
   │     redistributed. Provided as methodological reference.       │
   └────────────────────────────────────────────────────────────────┘
```

### What is and isn't reproducible from this repo + Zenodo

| Stage | Reproducible from clone + Zenodo? | Why / what's needed |
|---|---|---|
| `i` image processing | **No** — needs raw cycleHCR microscopy stacks | Multi-TB raw data is not on Zenodo. The pipeline scripts (`Step_1_loop.sh` … `Step_5_spot_assignment.sh`, plus the Step_4_1 / Step_6 / Step_7 Dockerfiles) and the Nextflow workflow from `CycleHCR-Pipeline` are provided for reference; to re-run, follow `README.md` env #1 and supply your own raw stacks. |
| `ii` cell clustering | **Yes** | `input.zip` on Zenodo → `ii_whole_brain_cell_clustering/input/`. |
| `iii` ML classification | **Yes** | QuAC raw images on Zenodo → `iii_ML_classification/input/`; `all_cells_ave_int_5_leiden.h5ad` is produced by running the `ii` UMAP/clustering notebooks. |
| `iv` QuAC | **Yes** (training is GPU-bound, see runtime below) | QuAC raw images on Zenodo + `iv_QuAC_explainable_ML/QuAC_config_neuron_H3K4me1.yaml`. |
| `v` QuAC feature quantitation | **Yes** | QuAC raw image dataset on Zenodo (shared with `iii` and `iv`). |
| `vi` cell-culture pipeline | **No** | Raw `.nd2` / `.tiff` cell-culture stacks acquired by the authors; not redistributed. Provided as methodological reference. |
| `vii` robustness tests | **Yes** | `input.zip` on Zenodo → `vii_Clustering_robustness_tests/input/`. |

---

## 2. Per-section walkthrough

Each block lists: **Goal · Environment · Inputs · Notebooks (in order) · Outputs · Hardware / runtime.** "Environment" names refer to the five environments in `README.md § Computational environments`.

### i. Whole-brain image processing
*Folder: `i_whole_brain_image_processing_pipeline/`*

- **Goal.** Stitch, register, segment and quantify the whole-brain cycleHCR volume; produce per-cell nuclear-protein intensity tables and the per-cell 3D nuclear image dataset that feeds sections `iii`, `iv`, and `v`.
- **Environment.** Stitching / registration / spot-calling run as Nextflow processes under SingularityCE (`README.md` env #1). Nuclear segmentation (Step 4) and 3D nucleus cropping (Step 6) run in the Docker containers built from this folder (the distributed Cellpose container is `README.md` env #2). Step 7 and Step 12 run as **standalone Python scripts** in the analysis environment (`README.md` env #3, `requirements.txt`) — no Docker needed; edit the `USER CONFIG` block at the top of each script before running.
- **Inputs.** Raw cycleHCR imaging volumes (off-Zenodo; provided by the authors on request).
- **Driver scripts (in order):**
  1. `Step_1_loop.sh` — top-level loop driving the stitching / per-round preprocessing.
  2. `Step_2_BatchRegistration_wholebrain_v2.sh` — multi-round 3D registration via `scripts/bigstream_v2.sh`.
  3. `Step_3_rsFISH_s1.sh` — RNA-spot detection (radial-symmetry FISH).
  4. `Step_4_1_Cellpose_distributed_docker/` — distributed Cellpose nuclear segmentation. Run inside the Docker built from this folder's `Dockerfile`; entry point `entrypoint.sh` calls `Cellpose_distributed.py`.
  5. `Step_4_2_center_of_mass_whole_image.ipynb` — per-label centroid extraction from the segmentation mask.
  6. `Step_4_3_dilate_mask_for_RNA_spot_assignment.ipynb` — mask dilation for spot-to-cell assignment.
  7. `Step_5_spot_assignment.sh` — assign RNA spots to nuclei using the dilated mask.
  8. `Step_6_Nuclear_3D_image_cropping_docker/` — per-cell 3D crops. Run inside the Docker built from this folder's `Dockerfile`; driver shell scripts `crop_open.sh`, `crop_s0.sh`, calling `scripts/bigstream_segment_s0_parallel.py` and `scripts/fix_segment_s0.py`.
  9. `Step_7_and_12_nuclei_measure_and_write_ML_images/Step_7_measure_nucleus_intensity.py` — per-cell nuclear-protein intensity measurements. Standalone Python script (analysis env, no Docker): edit the `USER CONFIG` block, then `python Step_7_measure_nucleus_intensity.py`.
  10. `Step_7_and_12_nuclei_measure_and_write_ML_images/Step_12_write_ML_image_dataset.py` — packages per-cell crops into the **QuAC raw image dataset** that becomes the Zenodo deposit consumed by `iii`, `iv`, `v`. Standalone Python script (analysis env, no Docker); requires the pre-assigned cell-ID list from `ii` Step_11. Edit the `USER CONFIG` block, then `python Step_12_write_ML_image_dataset.py`.
- **Outputs that downstream sections consume (via Zenodo, not direct file passing):**
  - Per-cell intensity h5ads + `center_of_mass_results.csv` → bundled into `input.zip` for `ii`.
  - Per-cell 3D nuclear image dataset → uploaded as the QuAC raw images on Zenodo (input for `iii`, `iv`, `v`).
- **Hardware / runtime.** HPC cluster with Singularity; GPU recommended for Cellpose. End-to-end runtime depends on the cluster.

### ii. Whole-brain cell clustering
*Folder: `ii_whole_brain_cell_clustering/`*

- **Goal.** Build the integrated nuclear-protein and RNA UMAPs across the two brain sections; define the 26/27/33 cluster solutions used throughout the paper. Generates the `adata_*_leiden.h5ad` snapshots consumed by section `iii`.
- **Environment.** Analysis env (`omics-cyclehcr`, `README.md` env #3) for the notebooks; the two heatmap scripts (`Step_8_3`, `Step_9_3`) use the R env (`README.md` env #4).
- **Inputs.** Download `input.zip` from Zenodo ([10.5281/zenodo.18633455](https://doi.org/10.5281/zenodo.18633455)) and unzip into `ii_whole_brain_cell_clustering/input/`. The folder contains:
  | File | Used by |
  |---|---|
  | `adata_18_nuclear_46_prot_brain1.h5ad`, `brain2_nuclear_int_18prot.h5ad` | 8_2, 8_4, 10 |
  | `RNA_processed_2nd_brain.h5ad` | 9_1, 9_2, 9_4 |
  | `cell_by_transcript_gene_name_matrix{1,2}.csv` | 9_1 |
  | `center_of_mass_results.csv` | 8_1, 9_4, 10, 11 |
  | `R_*.csv` | 8_3 (R), 9_3 (R) |
- **Notebooks, in order:**
  1. `Step_8_1_Nuclear_protein_intensity_preprocess.ipynb` → `output/adata_18_nuclear_46_prot_brain1.h5ad`
  2. `Step_8_2_Nuclear_protein_intensity_UMAP_2_brains.ipynb` → 2-brain Harmony-corrected protein UMAP; writes `adata_plot_harmony_ave_int_2_brains.h5ad` and per-brain h5ads.
  3. `Step_8_3_heatmap_nuclear_protein.R` — pheatmap of the protein z-score matrix.
  4. `Step_8_4_Protein_intensity_2brains_correlation.ipynb` — cross-brain protein correlation.
  5. `Step_9_1_RNA_preprocessing_and_replicate_correlation.ipynb` → `output/filtered_RNA_matrix.h5ad`
  6. `Step_9_2_RNA_UMAP_2_brains.ipynb` → `harmony_RNA_2_brains.h5ad`, per-brain RNA h5ads.
  7. `Step_9_3_heatmap_RNA.R` — pheatmap of the RNA z-score matrix.
  8. `Step_9_4_Plot_each_gene_spatial_profile.ipynb` — per-gene spatial profile plots.
  9. `Step_10_One_brain_spatial_correlation.ipynb` — within-brain left/right correlation figure.
  10. `Step_11_cell_ID_list_random_sampling.ipynb` — sample per-cluster cell-ID lists used by section `i` Step_6 (3D cropping) and by section `iii`.
- **Outputs that downstream sections consume:** `adata_plot_harmony_ave_int_2_brains.h5ad` (→ `iii`, `vii`); `harmony_27_clusters_*_brain.h5ad` (→ `vii`); the `all_cells_ave_int_*_leiden.h5ad` AnnData consumed by `iii`.
- **Hardware / runtime.** Single workstation, CPU sufficient. Harmony on the full 2-brain dataset is ~30 min; UMAP another 5–10 min.

### iii. ML classification
*Folder: `iii_ML_classification/`*

- **Goal.** (12) Classify per-cell cropped nuclear images by Monai/PyTorch into the protein-UMAP cluster labels; (13) measure how classification performance scales with the number of protein channels and rank channels by SHAP importance.
- **Environment.** Analysis env (`README.md` env #3). GPU strongly recommended for `Step_12`.
- **Inputs.**
  - QuAC raw image dataset from Zenodo ([10.5281/zenodo.18633455](https://doi.org/10.5281/zenodo.18633455)) — per-cell 3D nuclear crops shared with `iv` and `v`. Unzip into `iii_ML_classification/input/`.
  - `all_cells_ave_int_5_leiden.h5ad` — produced by running section `ii`'s UMAP + clustering notebooks.
  - `cell_by_transcript_gene_name_matrix2.csv` — already in `ii_whole_brain_cell_clustering/input/`.
- **Notebooks, in order:**
  1. `Step_12_Monai_classification.ipynb` — train + evaluate Monai classifier on the per-cell crops.
  2. `Step_13_ML_number_of_proteins_and_importance.ipynb` — sweep number of channels, compute summary stats, SHAP-rank channels.
- **Outputs.** `all_results_detailed.csv`, `summary_statistics.csv`, `classification_Num_proteins.pdf`, `shap_bar.eps`, `shap_violin_cluster_{i}.pdf`, `umap_leiden_rasterized.pdf`, `spatial_clusters.pdf`.
- **Hardware / runtime.** GPU (CUDA) for training; minutes to a couple of hours depending on the channel sweep.

### iv. QuAC explainable ML
*Folder: `iv_QuAC_explainable_ML/`*

- **Goal.** Discover cell-type-specific nuclear sub-structures via counterfactual generation.
- **Environment.** QuAC env (`README.md` env #5): Linux x86_64, CUDA 11.8, dedicated GPU.
- **Inputs.** QuAC raw image dataset on Zenodo (shared with `iii` and `v`; per-cell 3D nuclear crops produced by section `i`).
- **Procedure.**
  1. Install QuAC per `README.md` env #5 (pinned to commit `ce13955b9ad999c8b4673cbfb0b51bce72a551ea`).
  2. Run the QuAC pipeline using `QuAC_config_neuron_H3K4me1.yaml` (this folder) as the experiment config. See https://funkelab.github.io/quac/ for the full QuAC workflow.
- **Hardware / runtime.**
  - **Training is the only computationally heavy step:** ~**9 hours for 4-class** models and ~**14 hours for 8-class** models at **40,000 iterations** on our hardware.
  - All other QuAC steps (attribution, counterfactual generation, evaluation) are fast — each typically completes within ~**20 minutes** for our datasets.

### v. QuAC feature quantitation
*Folder: `v_QuAC_feature_quantitation/`*

- **Goal.** Population-level quantitative validation of QuAC-identified nuclear features (puncta intensity / count, radial distribution) across the full cell population.
- **Environment.** Analysis env (`README.md` env #3).
- **Inputs.** QuAC raw image dataset on Zenodo (shared with `iii` and `iv`; per-cell `.tiff` 3D nuclear crops).
- **Notebooks** (each independent — order arbitrary):
  - `a_H3K4me1 dataset quantitation.ipynb` → `H3K4me1_distribution.pdf`
  - `b_mH2A1 dataset puncta quantitation.ipynb` → `mH2A1_puncta_intensity_normalized_0_vs_1_range.pdf`
  - `c_DAPI puncta count dataset quantitation.ipynb` → `bright_puncta_distribution_1_3.pdf`
  - `Ext_Fig_cortex_H3K4me1_PolIIS5_dataset_radial_quantitation.ipynb` → `cortex_curves/*.pdf`
- **Hardware / runtime.** CPU; minutes per notebook.

### vi. Cell-culture pipeline
*Folder: `vi_cell_culture_image_processing/`*

- **Goal.** Per-cell nuclear-protein intensity quantification on cultured neurons + astrocytes, ending in a per-cell UMAP and cell-type cluster comparison.
- **Environment.** Analysis env (`README.md` env #3).
- **Inputs.** Raw `.nd2` / `.tiff` cell-culture stacks and intermediate measurement CSVs acquired by the authors; not redistributed. This section is provided as a methodological reference; reproducing it end-to-end requires equivalent cell-culture imaging data.
- **Notebooks, in order (when raw data is available):**
  1. `1_image_registration.ipynb` — register multi-timepoint cycleHCR `.nd2` stacks, write aligned `.tiff`.
  2. `3_Extract_nuclear_images_batch.ipynb` — segment nuclei + extract per-cell crops.
  3. `4_calculate_nuclear_protein_intensity.ipynb` — per-cell nuclear-protein intensity table.
  4. `5_GFAP_ave_intensity.ipynb` — astrocyte GFAP intensity (cell-type label).
  5. `6_Other_nuclei_measurements.ipynb` — auxiliary nuclear features.
  6. `7_UMAP_neuron_astrocyte_nuclear_protein_intensity.ipynb` — UMAP of the combined neuron + astrocyte intensity table.

### vii. Clustering robustness tests
*Folder: `vii_Clustering_robustness_tests/`*

- **Goal.** Reviewer-requested robustness checks: (a) Harmony parameter sensitivity; (b) PCA-vs-no-PCA + alternative clustering methods (Louvain / K-means / hierarchical / spectral); (c) random-seed Leiden reproducibility.
- **Environment.** Analysis env (`README.md` env #3).
- **Inputs.** Download `input.zip` from Zenodo ([10.5281/zenodo.18633455](https://doi.org/10.5281/zenodo.18633455)) and unzip into `vii_Clustering_robustness_tests/input/`. Contents:
  - `adata_18_nuclear_46_prot_brain1.h5ad`, `brain2_nuclear_int_18prot.h5ad`
  - `adata_plot_harmony_ave_int_2_brains.h5ad` (= published Harmony result)
  - `harmony_27_clusters_1st_brain.h5ad`
  - `cell_by_transcript_gene_name_matrix{1,2}.csv`
- **Notebooks (independent — order arbitrary):**
  - `Harmony_sensitivity_analysis.ipynb` — Harmony theta / lambda / sigma sweep.
  - `PCA_clustering_sensitivity_analysis_harmony.ipynb` — PCA-vs-scale + clustering-method sweep.
  - `Random_Clustering_reproducibility.ipynb` — Leiden random-seed reproducibility.
- **Outputs.** Written to `vii_Clustering_robustness_tests/output/` — ARI/NMI matrices, composite figures, etc.
- **Hardware / runtime.** CPU. Harmony sweeps in `Harmony_sensitivity_analysis.ipynb` dominate (~30 min × number of configs).

---
