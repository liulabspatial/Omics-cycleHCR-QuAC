"""Step 12: generation of ML training and validation image datasets.

Runs directly in a local python environment (see requirements.txt),

Needs a pre-assigned cell ID list from Step 11. For each selected cell, the middle
z-plane of the Step 6 cropped image is centered on a fixed canvas, converted to
8-bit, and written to <output_root>/<protein>/<assignment>/<protein_cluster>/.
"""

import os
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import tifffile

# ============================ USER CONFIG ============================
# --- input / output paths ---
image_root  = "./Step6_crop"               # cropped nuclear images (from Step 6)   <- change to your path
cell_id_csv = "selected_cell_IDs.csv"      # list of selected cell IDs + cluster assignments   <- change to your path
output_root = "./QUAC_images_all_cells"    # where the ML image dataset is written   <- change to your path

# --- processing parameters ---
max_workers = 10          # threads for parallel writing (large datasets)
large_shape = (90, 90)    # canvas size each cell image is centered into (y, x)
min_pixels  = 1500        # drop masks with fewer non-zero pixels than this

# Optional for big clusters. Clusters whose cropped images are split across two folders (<cluster>_1 / <cluster>_2)
split_clusters = {"0", "1", "2", "3", "4"}

# image filename pattern: reg_b#_t#_c#_s0_<cell_num>.tiff
pattern = re.compile(r"reg_(?P<code>b\d+_t\d+_c\d+)_s0_(?P<cell_num>\d+)\.tiff")

# nuclear markers and the image codes (b#_t#_c#) that map to each marker
targets = ['H3K27ac', 'H4K8ac', 'PolII S5p', 'SF3a66', 'CDK9', 'H3K4me1', 'HP1a', 'mH2A1', 'H3K4me3', 'MECP2',
           'Matrin3', 'CBP', 'H4K16ac', 'H2K119u1', 'DAPI']
x = ['b3_t4_c1', 'b3_t4_c2', 'b3_t5_c0', 'b3_t5_c1', 'b3_t5_c2', 'b3_t6_c0', 'b3_t6_c1', 'b3_t6_c2', 'b3_t7_c0',
     'b3_t7_c1', 'b3_t7_c2', 'b4_t0_c0', 'b4_t0_c2', 'b4_t1_c2', 'b4_t1_c3']
conversion = dict(zip(x, targets))

# column names in the cell id list csv
ID_COL, ASSIGN_COL, CLUSTER_COL, PROT_CLUSTER_COL = "cell_id", "assignment", "cluster", "protein_cluster"
# =====================================================================


def process_image_to_fit(small_image, large_shape):
    small_shape = small_image.shape
    large_image = np.zeros(large_shape, dtype=np.uint16)

    if all(s <= l for s, l in zip(small_shape, large_shape)):
        start_z = (large_shape[0] - small_shape[0]) // 2
        start_y = (large_shape[1] - small_shape[1]) // 2
        large_image[start_z:start_z + small_shape[0], start_y:start_y + small_shape[1]] = small_image.astype(np.uint16)
    else:
        start_z = max((large_shape[0] - small_shape[0]) // 2, 0)
        start_y = max((large_shape[1] - small_shape[1]) // 2, 0)

        crop_start_z = max((small_shape[0] - large_shape[0]) // 2, 0)
        crop_start_y = max((small_shape[1] - large_shape[1]) // 2, 0)

        crop_end_z = crop_start_z + min(small_shape[0], large_shape[0])
        crop_end_y = crop_start_y + min(small_shape[1], large_shape[1])

        large_image[
            start_z:start_z + (crop_end_z - crop_start_z),
            start_y:start_y + (crop_end_y - crop_start_y)
        ] = small_image[crop_start_z:crop_end_z, crop_start_y:crop_end_y].astype(np.uint16)

    return large_image


def convert_to_8bit(image):
    image = image.astype(np.float32)
    min_val = image.min()
    max_val = image.max()
    if max_val > min_val:
        image = (image - min_val) / (max_val - min_val) * 255
    else:
        image = np.zeros_like(image)
    return image.astype(np.uint8)


def write_images_for_cells(cell_numbers, image_index, conversion_table, cell_to_assignment, large_shape):
    #target_proteins = {"H3K4me1", "mH2A1"}
    for key, protein in conversion_table.items():
        #if protein not in target_proteins:  # Only process this protein
            #continue

        for cell_number in cell_numbers:
            if cell_number not in cell_to_assignment:
                continue

            code_to_file = image_index.get(cell_number, {})
            if key not in code_to_file:
                print(f"[Missing] protein {key} not found for cell {cell_number}")
                #print(f"Available proteins: {list(code_to_file.keys())}")
                #print(f"Available image files for cell {cell_number}: {list(code_to_file.values())}")
                continue

            source_path = code_to_file[key]
            new_name = f'cell{cell_number}.tiff'

            assignment = cell_to_assignment[cell_number]["assignment"]
            cluster_str = cell_to_assignment[cell_number]["protein_cluster"]

            dest_folder = f'{output_root}/{protein}/{assignment}/{cluster_str}/'
            os.makedirs(dest_folder, exist_ok=True)

            destination_path = os.path.join(dest_folder, new_name)

            try:
                image_tiff = tifffile.imread(source_path)
                z_plane = image_tiff.shape[0] // 2               #  extract middle z-plane
                new_image = image_tiff[z_plane, :, :]

                centered_image = process_image_to_fit(new_image, large_shape)

                # filter out small broken masks
                if np.count_nonzero(centered_image) < min_pixels:
                    print(f"[Skipped] cell {cell_number}, protein {protein} - too few pixels")
                    continue

                centered_image_8bit = convert_to_8bit(centered_image)

                tifffile.imwrite(destination_path, centered_image_8bit)
                print(f"[Written] {destination_path}")
            except Exception as e:
                print(f"[Error] Writing image for cell {cell_number}, protein {protein}: {e}")


def run_write_image_multithreaded(cluster_to_cells, image_index, conversion_table, cell_to_assignment, large_shape, max_workers=10):    # multi-thread for large datasets
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for cluster, cell_numbers in cluster_to_cells.items():
            futures.append(
                executor.submit(
                    write_images_for_cells, cell_numbers, image_index, conversion_table, cell_to_assignment, large_shape
                )
            )

        total = len(futures)
        completed = 0

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"[Error] Exception in write_image: {e}")

            completed += 1
            print(f"[Progress] Processed {completed}/{total} clusters")


def main():
    df = pd.read_csv(cell_id_csv)

    df[ID_COL] = df[ID_COL].astype(int)  # make sure cell_id is int for matching with image_index keys
    df[PROT_CLUSTER_COL] = df[PROT_CLUSTER_COL].astype(str)
    df[CLUSTER_COL] = df[CLUSTER_COL].astype(str)

    cell_to_assignment = df.set_index(ID_COL)[[ASSIGN_COL, CLUSTER_COL, PROT_CLUSTER_COL]].to_dict(orient="index")

    cell_ids = set(df[ID_COL])

    protein_clusters = sorted(df[PROT_CLUSTER_COL].unique())
    # clusters column has the folder names
    clusters = sorted(df[CLUSTER_COL].astype(float).astype(int).astype(str).unique())

    all_folders = set()
    for cluster in clusters:                 # split_clusters (large cell counts) are stored in 2 folders each
        if cluster in split_clusters:
            all_folders.add(os.path.join(image_root, f"{cluster}_1"))
            all_folders.add(os.path.join(image_root, f"{cluster}_2"))
        else:
            all_folders.add(os.path.join(image_root, f"{cluster}"))

    print(f"Scanning {len(all_folders)} folders...")

    cluster_counts = Counter(df[PROT_CLUSTER_COL])
    for cluster, count in sorted(cluster_counts.items(), key=lambda x: int(x[0])):
        print(f"Protein cluster {cluster}: {count} cells")

    image_index = {}
    for folder in all_folders:
        #print(folder)
        if not os.path.exists(folder):
            continue

        for filename in os.listdir(folder):
            match = pattern.match(filename)
            if not match:
                #print(f"[Unmatched filename] {filename} in {folder}")
                continue

            code = match.group("code")
            cell_number = int(match.group("cell_num"))

            if cell_number not in image_index:
                image_index[cell_number] = {}

            image_index[cell_number][code] = os.path.join(folder, filename)

    # Build cluster_to_cells dict: cluster string -> list of cell_ids
    cluster_to_cells = df.groupby(PROT_CLUSTER_COL)[ID_COL].apply(list).to_dict()

    run_write_image_multithreaded(cluster_to_cells, image_index, conversion, cell_to_assignment, large_shape, max_workers=max_workers)


if __name__ == '__main__':
    main()
