def main():
    print("Hello from inside the cell_measurement container!")
    import os
    import re
    import tifffile
    import pandas as pd
    import numpy as np
    import anndata


    # nuclear markers and the corresponding channel names in image files
    targets = ['H3K27ac','H4K8ac','PolII S5p','SF3a66','CDK9', 'H3K4me1', 'HP1a', 'mH2A1', 'H3K4me3', 'MECP2',
               'Matrin3','CBP', 'H4K16ac','H2K119u1','DAPI']


    x = ['b3_t4_c1','b3_t4_c2','b3_t5_c0','b3_t5_c1','b3_t5_c2','b3_t6_c0','b3_t6_c1','b3_t6_c2','b3_t7_c0','b3_t7_c1','b3_t7_c2','b4_t0_c0',
                  'b4_t0_c2', 'b4_t1_c2', 'b4_t1_c3']

    conversion_dict = dict(zip(x, targets))

    # where cropped nuclear images are stored with subfolders
    base_dir = "/home/liulab/labdata/wholebrain_output/Step6_crop"

    # nuclear intensity was stored in h5ad files for each subfolder
    for folder_id in range(0, 26):
        input_dir = os.path.join(base_dir, str(folder_id))
        output_h5ad = os.path.join(base_dir, f"avg_intensity{folder_id}.h5ad")

        print(f"\nInput Directory   : {input_dir}")
        print(f"Output .h5ad File : {output_h5ad}")

        data = []

        # read filenames of cropped images
        for fname in os.listdir(input_dir):
            if fname.endswith(".tiff") and fname.startswith("reg_"):
                match = re.match(r"reg_(b\d+_t\d+_c\d+)_s0_(\d+).tiff", fname)
                if not match:
                    print(f"Skipping unrecognized file format: {fname}")
                    continue

                chan_id, cell_id = match.groups()
                protein = conversion_dict.get(chan_id)
                if protein is None:
                    continue  # skip unknown channels

                img_path = os.path.join(input_dir, fname)
                img = tifffile.imread(img_path)
                avg_intensity = img[img > 0].mean() if np.any(img > 0) else 0.0

                data.append({
                    "cell": str(cell_id),
                    "protein": protein,
                    "avg_intensity": avg_intensity
                })

        # Create matrix
        df_long = pd.DataFrame(data)
        df_wide = df_long.pivot(index="cell", columns="protein", values="avg_intensity").fillna(0)
        df_wide = df_wide[(df_wide != 0).all(axis=1)]  # drop rows with any zero

        # Build AnnData object
        adata = anndata.AnnData(
            X=df_wide.to_numpy(),
            obs=pd.DataFrame(index=df_wide.index.astype(str)),
            var=pd.DataFrame(index=df_wide.columns.astype(str))
        )

        adata.obs_names = df_wide.index.astype(str)
        adata.var_names = df_wide.columns.astype(str)

        adata.write(output_h5ad)
        print(f"Saved to {output_h5ad}")

if __name__ == '__main__':
    main()
