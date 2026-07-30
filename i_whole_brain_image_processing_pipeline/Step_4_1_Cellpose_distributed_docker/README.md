# Distributed Cellpose (Docker)

Whole-brain 3D nuclear segmentation with Cellpose, parallelized over image
blocks with `cellpose.contrib.distributed_segmentation` (Dask).
See documentation page for usage:
[https://cellpose.readthedocs.io/en/latest/distributed.html](https://cellpose.readthedocs.io/en/latest/distributed.html). 
The Docker image bundles the exact pinned environment so it runs on any 
machine with a CUDA GPU.

## Environment (pinned in the Dockerfile)

- Base image `condaforge/miniforge3`, Python 3.10
- Cellpose (MouseLand) commit `15eb3c6`
- PyTorch 2.7.1 / torchvision 0.22.1 (CUDA 12.6 build)
- zarr 2.18.3, dask-image 2026.5.0, dask 2026.6.0, dask-jobqueue 0.9.0

## 1. Build

From inside this folder:

    docker build -t cellpose-distributed .

## 2. Run

Put your input image in a `data/` folder next to this README, then:

    docker run --gpus all -v ${PWD}/data:/data -w /data cellpose-distributed

- `-v ${PWD}/data:/data` mounts your local `data/` folder into the container.
- `-w /data` sets the working directory to that folder, so the script reads its
  input from `/data` and writes outputs back into your local `data/`.
- No command is needed: the image's `ENTRYPOINT` activates the `cellpose` conda
  environment and the default `CMD` runs `python /app/Cellpose_distributed.py`.

A CUDA-capable GPU is required (`--gpus all`).

To open an interactive shell with the environment active instead:

    docker run --gpus all -it -v ${PWD}/data:/data -w /data cellpose-distributed bash

## 3. Inputs and outputs

Input filenames and all segmentation parameters are set at the top / body of
`Cellpose_distributed.py`:

- **Intensity image** (DAPI channel) — read from `DAPI.tif` by default. Put your
  file at `data/DAPI.tif`, or edit the name in the script.
- **Mask** (optional) — a binary mask restricting segmentation to tissue, read
  from `mask.tif`. If you don't have one, comment out **both** the
  `mask_ar = tifffile.imread('mask.tif')` line and the `mask=mask_ar` argument in
  `distributed_eval(...)`, otherwise the run stops at `/data/mask.tif`.
- Key parameters: `blocksize`, `do_3D`, and the Dask
  `cluster_kwargs` (`n_workers`, `ncpus`, `memory_limit`) — tune to your data and
  hardware.

Outputs are written to the working directory (`/data` → your local `data/`):

- `fix_scaled.zarr` — intermediate zarr copy of the input (created automatically)
- `output.zarr` — label array
- `segment_output.tiff` — labels as TIFF

> Note: run with `-w /data` (as above) so outputs persist to the host. Without
> it, the script reads/writes in the image's `/app` directory and the results are
> lost when the container exits.
