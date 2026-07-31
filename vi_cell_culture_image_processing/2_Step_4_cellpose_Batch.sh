# Cell segmentation was performed on HPCs to handle large memory using previously published workflow
# https://github.com/liulabspatial/CycleHCR-Pipeline/tree/main

# This customized code is for processing multiple images from different fields of view collected on cell cultures.

# Modify parameters at the end of the code to your minimum nuclear voxel threshold (-m), nuclear diameter (-d) 
# and trained models (--model_xy, --model_yz)

# === Configure these paths for your environment (or set as environment variables) ===
inputpath="${INPUT_PATH:-/path/to/time1_z_rescaled_DAPI_imgs/}"   # <- change to your path
outputpath="${OUTPUT_PATH:-/path/to/CP_masks4/}"   # <- change to your path
# Cellpose pipeline executable and models (from the CycleHCR-Pipeline repo)
cellpose="${CELLPOSE_SCRIPT:-/path/to/scripts/cellpose.sh}"   # <- change to your path
model_xy="${MODEL_XY:-/path/to/models/CP_neuron_xy5}"   # <- change to your path
model_yz="${MODEL_YZ:-/path/to/models/CP_neuron_yz5}"   # <- change to your path

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
        "$cellpose" \
              -i $file \
              -o $outputdir \
              -m 20000 -d 70\
              --model_xy "$model_xy" \
              --model_yz "$model_yz"
done
