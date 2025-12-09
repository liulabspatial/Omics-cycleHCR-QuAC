# Cell segmentation was performed on HPCs to handle large memory using previously published workflow
# https://github.com/liulabspatial/CycleHCR-Pipeline/tree/main

# This customized code is for processing multiple images from different fields of view collected on cell cultures.



inputpath="/home/liulab/labdata/Yumin/Neuron/time1_z_rescaled_DAPI_imgs/"
outputpath="/home/liulab/labdata/Yumin/Neuron/CP_masks4/"

# Specify the directory to check
dir=$outputpath

# Check if the directory exists
if [ ! -d "$dir" ]; then
    # The directory does not exist, create it
    mkdir -p "$dir"
    echo "Directory created: $dir"
else
    echo "Directory already exists: $dir"
fi

# Setting the suffix and populating the array with filenames
suffix="*.tif"
files=("${inputpath}"${suffix})

# Initialize the counter
i=1

# Process each file

for file in "${files[@]}"
do
        outputdir="${outputpath}z${i}.tif"  # Construct the output directory name
      	((i++))  # Increment the counter
        echo "Processing $file"
        echo "Output will be in $outputdir"
        /home/liulab/labdata/scripts/cellpose.sh \
              -i $file \
              -o $outputdir \
              -m 20000 -d 70\
              --model_xy /home/liulab/labdata/Yumin/Neuron/models/CP_neuron_xy5 \
              --model_yz /home/liulab/labdata/Yumin/Neuron/models/CP_neuron_yz5
done
