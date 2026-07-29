import numpy as np
import zarr
import tifffile
import pandas as pd
import scipy.ndimage
from scipy.ndimage import find_objects
from bigstream.transform import apply_transform_to_coordinates, apply_transform
from bigstream.align import alignment_pipeline

import sys
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed   # or ProcessPoolExecutor
import multiprocessing

import argparse
import gc


# check create directory #
def check_create_dir(path):
    os.makedirs(path, exist_ok=True)
    print(f"Directory ready: {path}")

# extract batch and time point to generate outfile name prefix #
def get_batch_time(N5path):
    S = N5path.split('/')[-3:] # split by /
    for s in S:
        if (len(s) in [2,3,4]) and s.startswith("b") and any(char.isdigit() for char in s):  # look for string that has length of 2,3,4 and starts with b and contains a number
            B = s
        elif (len(s) in [2,3,4]) and s.startswith("t") and any(char.isdigit() for char in s): # look for string that has length of 2,3,4 and starts with t and contains a number
            T = s
    return B,T

def get_channels(N5path):
    return sorted([s for s in os.listdir(N5path) if len(s) == 2 and s.startswith("c")])

# returns list of start coordinates and list of stop coordinates
def get_crop_coordinates(seg, idx_lst):
    # Find all label bounding boxes in one pass
    slices = find_objects(seg)

    zyxi_lst = []
    zyxf_lst = []

    for label in idx_lst:
        if label <= 0 or label > len(slices) or slices[label - 1] is None:
            continue  # label not found

        sl = slices[label - 1]  # slice object for label
        min_coords = [s.start for s in sl]
        max_coords = [s.stop - 1 for s in sl]  # inclusive max

        zyxi_lst.append(min_coords)
        zyxf_lst.append(max_coords)

    return np.array(zyxi_lst), np.array(zyxf_lst)


##### generate crop from start/stop coordinates #######
def make_crop(img,zyxi,zyxf):
    region = tuple(slice(a, b) for a, b in zip(zyxi,zyxf))
    crop = img[region]
    return crop



## assumes segmentation was done in same resolution as transformation matrix
def get_warped_crop_coordinates(seg,idx_lst,spacing_seg,transform,spacing_target):


    ### start/stop of crop coordinates in segmentation data (fix image) ###
    zyxi_seg,zyxf_seg = get_crop_coordinates(seg,idx_lst)

    ### obtain start/stop coordinates in mov data, better to be 'inclusive', not necessarily have to be in same shape as fix crop ###
    #
    zyxi_warp = apply_transform_to_coordinates(
        zyxi_seg * spacing_seg ,
        transform_list=[transform],
        transform_spacing=spacing_seg,
        )
    zyxf_warp = apply_transform_to_coordinates(
        zyxf_seg * spacing_seg ,
        transform_list=[transform],
        transform_spacing=spacing_seg,
        )

    ### add padding +/-10 voxels ###
    zyxi_warp_padded_target = np.round(zyxi_warp / spacing_target).astype(int)
    zyxi_warp_padded_target -= 10
    zyxf_warp_padded_target = np.round(zyxf_warp / spacing_target).astype(int)
    zyxf_warp_padded_target += 10

    print(zyxi_warp_padded_target,zyxf_warp_padded_target)
    start = np.array(zyxi_warp_padded_target).copy()
    start[start<0] = 0
    end = np.array(zyxf_warp_padded_target).copy()
    end[end<0] = 0

    return start, end

def all_output_files_exist(idx, channels, movBT, args_outdir):
    for c in channels:
        outfile_prefix = f"reg_{movBT[0]}_{movBT[1]}_{c}_s0_{idx}"
        outfile_tiff = os.path.join(args_outdir, outfile_prefix + ".tiff")
        if not os.path.exists(outfile_tiff):
            return False
    return True


def process_index_chunk(chunk, args, spacing_s0, spacing_seg, transform, dapi, fixBT, movBT):
    """
    Process a chunk of cell indices: extract, register, and save aligned cell crops.

    This function performs local cell-level registration after global alignment.
    """

    seg = tifffile.imread(args.seg)

    # Compute local coordinates for chunk
    idx_list = [idx for _, idx in chunk]
    zyxi_sSeg, zyxf_sSeg = get_crop_coordinates(seg=seg, idx_lst=idx_list)

    # Convert segmentation coordinates to s0 (full resolution) coordinates
    # by scaling according to the resolution ratio
    zyxi_s0 = np.round(zyxi_sSeg * spacing_seg / spacing_s0).astype(int)
    zyxf_s0 = np.round(zyxf_sSeg * spacing_seg / spacing_s0).astype(int)

    # Get warped coordinates in moving image space after applying global transform
    # These account for the global alignment between fix and mov images
    zyxi_warp_s0, zyxf_warp_s0 = get_warped_crop_coordinates(
        seg=seg, idx_lst=idx_list,
        spacing_seg=spacing_seg,
        transform=transform,
        spacing_target=spacing_s0
    )

    # Open zarr stores inside worker
    fix_zarr = zarr.open(store=zarr.N5FSStore(args.fixdir), mode='r')
    mov_zarr = zarr.open(store=zarr.N5FSStore(args.movdir), mode='r')
    # Get list of all channels in the moving image
    mov_channels = get_channels(args.movdir)

    for j, (_, idx) in enumerate(chunk):
        # Check if all output files already exist for this cell
        if all_output_files_exist(idx, mov_channels, movBT, args.outdir):
            print(f"Skipping cell {idx} — all outputs already exist.")
            continue

        # --- Extract fix crop image (DAPI channel from reference image) ---
        try:
            fix_crop = make_crop(fix_zarr[dapi + '/s0'], zyxi_s0[j], zyxf_s0[j]).copy()
        except IndexError:
            print(f"Skipping j={j}: index out of bounds")
            continue

        # Segmentation crop (binary mask)
        seg_crop = make_crop(seg, zyxi_sSeg[j], zyxf_sSeg[j])
        seg_bin = seg_crop == idx
        seg_crop[seg_bin] = 1
        seg_crop[~seg_bin] = 0
        seg_crop = seg_crop.astype('uint8')
        # Upsample segmentation mask to s0 resolution
        seg_crop_s0 = scipy.ndimage.zoom(seg_crop, zoom=np.divide(spacing_seg, spacing_s0), order=0)

        if any(dim < 4 for dim in seg_crop_s0.shape):
            print(f"Skipping segment {idx} — too small for registration: {seg_crop_s0.shape}")
            continue

         # Filter out cells with volume < 1500 voxels
        cell_volume = np.sum(seg_crop_s0)  # counts foreground voxels
        if cell_volume < 1500:
            print(f"Skipping segment {idx} — too small volume: {cell_volume}")
            continue

        # Moving crop (DAPI channel from image to be aligned)
        mov_crop = make_crop(mov_zarr[dapi + '/s0'], zyxi_warp_s0[j], zyxf_warp_s0[j]).copy()

        # Apply global transform
        # Transform the moving crop to roughly align with fix using pre-computed global transform
        mov_crop_transform = apply_transform(
            fix=fix_crop,
            mov=mov_crop,
            fix_spacing=spacing_s0,
            mov_spacing=spacing_s0,
            transform_list=[transform],    # Global transform from whole-image registration
            transform_spacing=spacing_seg,
            fix_origin=zyxi_s0[j] * spacing_s0,
            mov_origin=zyxi_warp_s0[j] * spacing_s0,
            interpolator='1'
        )

        # Local cell-level registration
        affine_kwargs = {
            'alignment_spacing': 1.0,
            'shrink_factors': (1,),
            'smooth_sigmas': (0.25,),
            'optimizer_args': {
                'learningRate': 0.25,
                'minStep': 0.0,
                'numberOfIterations': 20,
            },
        }

        deform_kwargs = {
            'alignment_spacing': 1.0,
            'shrink_factors': (1,),
            'smooth_sigmas': (0.25,),
            'control_point_spacing': 1,
            'control_point_levels': (1,),
            'optimizer_args': {
                'learningRate': 0.25,
                'minStep': 0.0,
                'numberOfIterations': 20,
            },
        }

        crop_transform_i = alignment_pipeline(
            fix=fix_crop,
            mov=mov_crop_transform,
            fix_spacing=spacing_s0,
            mov_spacing=spacing_s0,
            steps=[('affine', affine_kwargs)]  #, ('deform', deform_kwargs)]    # skip deform for images with big z-steps
        )

        # Apply transform to all channels and save
        for c in mov_channels:
            mov_chan_crop = make_crop(mov_zarr[str(c) + '/s0'], zyxi_warp_s0[j], zyxf_warp_s0[j]).copy()

            # Apply global transform to this channel
            mov_chan_transform = apply_transform(
                fix=fix_crop,
                mov=mov_chan_crop,
                fix_spacing=spacing_s0,
                mov_spacing=spacing_s0,
                transform_list=[transform],
                transform_spacing=spacing_seg,
                fix_origin=zyxi_s0[j] * spacing_s0,
                mov_origin=zyxi_warp_s0[j] * spacing_s0,
                interpolator='1'
            )

            # Apply local cell-specific transform
            mov_chan_transform2 = apply_transform(
                fix=fix_crop,
                mov=mov_chan_transform,
                fix_spacing=spacing_s0,
                mov_spacing=spacing_s0,
                transform_list=[crop_transform_i],
                interpolator='1'
            )

            # Mask the result to only include this cell
            result = np.multiply(mov_chan_transform2, seg_crop_s0)

            if result.size == 0 or result.ndim != 3 or 0 in result.shape:
                print(f"Skipping output for segment {idx}, channel {c} — invalid shape: {result.shape}")
                continue

            # Save registered and masked cell crop
            outfile_prefix = f"reg_{movBT[0]}_{movBT[1]}_{c}_s0_{idx}"
            outfile_tiff = os.path.join(args.outdir, outfile_prefix + ".tiff")
            tifffile.imwrite(outfile_tiff, result, imagej=True, metadata={'axes': 'ZYX'})

        del fix_crop, mov_crop, mov_crop_transform, crop_transform_i, seg_crop_s0
        gc.collect()
        # Free memory

def main():
    """
    Main entry point: Parse arguments, load data, and distribute work across threads.
    """

    max_idx = 342258   # specify the largest mask ID to stop in the last batch

    print(f"Worker PID {os.getpid()}, CPUs allowed: {os.sched_getaffinity(0)}")
    multiprocessing.set_start_method("fork", force=True)

    # Parse command-line arguments
    usage_text = ("Usage:" + " .py -n ../b0/t1 -td ../step2/transform/ -seg ../step4/Mask_b0_t0_c3_s2.tiff, -idx 1000 -o ../step?/")
    parser = argparse.ArgumentParser(description=usage_text,usage=argparse.SUPPRESS)
    parser.add_argument('-f','--fixdir',dest='fixdir',type=str,help='path to fix N5',required=True,metavar='')
    parser.add_argument('-m','--movdir',dest='movdir',type=str,help='path to mov N5, for which the transform matrix exists',required=True,metavar='')
    parser.add_argument('-td','--transformdir',dest='transformdir',type=str,help='path to transformdir',required=True,metavar='')
    parser.add_argument('-seg','--segmentation',dest='seg',type=str,help='path to segmentation mask',required=True,metavar='')
    parser.add_argument('-idx','--index',dest='idx_lst',type=str,help='comma separated list of indices of segments',required=True,metavar='')
    parser.add_argument('-o','--outdir',dest='outdir',type=str,help='output directory',required=True,metavar='')
    args=parser.parse_args()

    check_create_dir(args.outdir)

    # Load metadata and compute spacing
    fix_zarr = zarr.open(store=zarr.N5FSStore(args.fixdir), mode='r')

    # Calculate physical spacing (in microns) for s0 resolution
    spacing_s0 = np.multiply(
        fix_zarr['c0/s0'].attrs.asdict()['pixelResolution'],
        fix_zarr['c0/s0'].attrs.asdict()['downsamplingFactors']
    )[::-1]

    # Parse segmentation filename to extract batch, time, channel, scale info
    seg_btcs = args.seg.split('/')[-1].split('.')[0].split('_')[1:]
    subpath = 'c0/' + str(seg_btcs[3])
    spacing_seg = np.multiply(
        fix_zarr[subpath].attrs.asdict()['pixelResolution'],
        fix_zarr[subpath].attrs.asdict()['downsamplingFactors']
    )[::-1]

    fixBT = get_batch_time(args.fixdir)
    movBT = get_batch_time(args.movdir)
    dapi = str(seg_btcs[2])

    # Construct path to pre-computed global transform
    transform_prefix = f"{fixBT[0]}_{fixBT[1]}_{dapi}_{seg_btcs[3]}-{movBT[0]}_{movBT[1]}_{dapi}_{seg_btcs[3]}"
    transform_path = os.path.join(args.transformdir, transform_prefix + '.npy')
    transform_checkpoint = os.path.join(args.transformdir, transform_prefix + '.checkpoint')

    # Check if global transform exists
    if not os.path.exists(transform_checkpoint):
        print('Transform matrix not found:', transform_checkpoint)
        return

    # Load the transform matrix
    transform = np.load(transform_path)

    # Parse cell index list     Support formats: "1,2,3" or "1-100" or "1,5-10,20"
    seg_idx_lst = []

    for part in args.idx_lst.split(','):
        part = part.strip()
        if '-' in part:
            start, end = map(int, part.split('-'))
            # Clip end to max available index
            end = min(end, max_idx)
            seg_idx_lst.extend(range(start, end + 1))
        else:
            idx = int(part)
            if idx <= max_idx:
                seg_idx_lst.append(idx)

    # Divide work into chunks for parallel processing
    all_indices = list(enumerate(seg_idx_lst))
    chunk_size = 100   # Process 100 cells per chunk
    chunks = [all_indices[i:i + chunk_size] for i in range(0, len(all_indices), chunk_size)]

    # Package shared arguments
    shared_args = (args, spacing_s0, spacing_seg, transform, dapi, fixBT, movBT)

    # Execute parallel processing
    max_workers = 10   # Use 10 threads
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all chunks to thread pool
        futures = [executor.submit(process_index_chunk, chunk, *shared_args) for chunk in chunks]
        for f in as_completed(futures):
            f.result()   # Retrieve result (will raise exception if chunk failed)


if __name__ == '__main__':
    main()
