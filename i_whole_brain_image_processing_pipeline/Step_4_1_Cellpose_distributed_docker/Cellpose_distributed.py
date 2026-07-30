def main():
    print("Hello from inside the Cellpose Docker container!")

    import numpy as np
    from cellpose import models, core, io, plot
    import zarr
    import tifffile


    model = models.CellposeModel(gpu=True)

    use_GPU = core.use_gpu()
    yn = ['NO', 'YES']
    print(f'>>> GPU activated? {yn[use_GPU]}')

    from cellpose.contrib.distributed_segmentation import distributed_eval
    # distributed_eval?

    from cellpose.contrib.distributed_segmentation import numpy_array_to_zarr


    data_numpy = tifffile.imread('DAPI.tif')  # change to your intensity image (DAPI channel) name
    print(data_numpy.shape)
    data_zarr = numpy_array_to_zarr('fix_scaled.zarr', data_numpy, chunks=(106, 512, 512))  # intermediate file, no need to supply
    # mask_ar = tifffile.imread('mask.tif')  # Optional. A binary mask restricting segmentation to tissue area

    model_kwargs = {'gpu':True}
    eval_kwargs = {
                   'z_axis':0,
                   'do_3D':True,
                   # 'stitch_threshold': 1
    }

     # define compute resources for local workstation
    cluster_kwargs = {
                       'n_workers':1,    # if you only have 1 gpu, then 1 worker is the right choice
                       'ncpus':20,
                       'memory_limit':'64GB',
                       'threads_per_worker':1,
     }

     # run segmentation
     # outputs:
     #     segments: zarr array containing labels
     #     boxes: list of bounding boxes around all labels (very useful for navigating big data)
    segments, boxes = distributed_eval(
         input_zarr=data_zarr,
         blocksize=(106, 512, 512),  # (106, 512, 512)
         write_path='output.zarr',
         # mask = mask_ar,                   # comment out if don't supply a mask image
         model_kwargs=model_kwargs,
         eval_kwargs=eval_kwargs,
         cluster_kwargs=cluster_kwargs,
    )

    segmented = zarr.open("output.zarr", mode='r')
    tifffile.imwrite('segment_output.tiff', segmented)

if __name__ == '__main__':
    main()
