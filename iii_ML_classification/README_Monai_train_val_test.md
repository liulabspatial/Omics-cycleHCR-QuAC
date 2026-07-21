# Monai_train_val_test.ipynb — cell-type classifier evaluation

**Evaluation / inference only.** This notebook runs the released MONAI
**DenseNet169** cell-type classifier on the held-out **test** split of a
train / val / test (70 / 10 / 20) partition and reproduces the reported numbers
and figure for one nuclear-marker channel (default **H3K4me1**). It does **not**
train — the training image data is not distributed, so the training loop,
optimizer/loss, ImageNet-pretrained init, and model-save steps have been removed.

The class list is auto-detected from the dataset folders; the folder-id → readable
name map lives in the notebook (`folder_to_class`), with unknown folders falling
back to their id.

## Configuration (no hard-coded paths)

Every input/output location is set in the **Configuration** cell at the top of the
notebook. Edit the defaults there, or override any of them without touching the
notebook by exporting the matching environment variable before launch:

| Variable              | Default                              | Meaning                                    |
| --------------------- | ------------------------------------ | ------------------------------------------ |
| `QUAC_CHANNEL`        | `H3K4me1`                            | Channel to evaluate                        |
| `QUAC_DATA_ROOT`      | `./QUAC_8_classes`                   | Root of the per-channel image datasets     |
| `QUAC_MODEL_ROOT`     | `./QUAC_model/eight_classes_model`   | Released DenseNet169 weights               |
| `QUAC_OUTPUT_ROOT`    | `./QUAC_8_classes`                   | Where the report / CSVs / figures are written |
| `QUAC_MAX_EPOCHS`     | `50`                                 | Epoch count baked into the weight filename |
| `QUAC_FONT_DIR`       | `C:/Windows/Fonts`                   | Arial Narrow location (Windows only; optional) |

```bash
QUAC_DATA_ROOT=/path/to/dataset \
QUAC_MODEL_ROOT=/path/to/models \
jupyter lab Monai_train_val_test.ipynb
```

`QUAC_DATA_ROOT` / `QUAC_MODEL_ROOT` default to the folders where the data and
weights currently live; point them anywhere via the env vars above.

## Expected on-disk layout

```
<QUAC_DATA_ROOT>/
    <CHANNEL>/
        test/<folder_id>/*.tiff      # held-out test crops (folder_ids: 0 5 8 11 13 16 19 22)

<QUAC_MODEL_ROOT>/
    <CHANNEL>_<MAX_EPOCHS>epochs_model.pth   # e.g. H3K4me1_50epochs_model.pth
```

Only the `test/` split is needed for evaluation.

## How to run

Run every cell top to bottom. The notebook loads `model_path(CHANNEL)`, runs
inference over the held-out `test/` split, prints the classification report, and
writes the outputs below.

## Outputs (written to `QUAC_OUTPUT_ROOT`)

- `<CHANNEL>_train_val_test_report.txt` — per-class precision/recall/F1 on the test split

The figure/CSV panel is regenerated from the same `y_true` / `y_pred`.

## Required intermediate files to deposit in the repo

So others can reproduce without the raw microscopy or a GPU retrain, deposit:

**Commit directly (small — belong in git):**
- `QUAC_8_classes/test_cell_ids.txt`, `QUAC_8_classes/val_cell_ids.txt`
  — the exact held-out val/test split used for the reported numbers.
- `<CHANNEL>_train_val_test_report.txt` and any confusion / per-class-F1 CSVs the
  notebook writes.

**Large — use Git LFS or an external archive (Zenodo / figshare), and link it here:**
- Released weights `QUAC_model/eight_classes_model/*.pth` (~49 MB each) — under
  GitHub's 100 MB per-file limit, so Git LFS works.
- The test image crops `QUAC_8_classes/<CHANNEL>/test/` — deposit as an external
  archive and put the download URL/DOI here.

> Data / weights DOI: _add link here before submission._

## Environment

See `requirements_Monai_train_val_test.txt`. Versions used for the reported runs:
MONAI 1.4.0, PyTorch 2.5.1, TorchVision 0.20.1, NumPy 1.26.4, pandas 2.0.3,
scikit-learn, seaborn, matplotlib. A CUDA GPU is used automatically if available,
otherwise the notebook falls back to CPU.
