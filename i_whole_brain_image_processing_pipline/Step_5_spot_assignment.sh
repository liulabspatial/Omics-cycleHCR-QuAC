# === Configure these paths for your environment (or set as environment variables) ===
spots_registered="${SPOTS_REGISTERED:-/path/to/wholebrain_output/Step3/spots_filtered/}"   # <- change to your path
segmentation_tif="${SEGMENTATION_TIF:-/path/to/wholebrain_output/Step5/dilated_s3.tiff}"   # <- change to your path
step5dir="${STEP5_DIR:-/path/to/wholebrain_output/Step5/}"   # <- change to your path
# Spot-assignment pipeline executable (from the CycleHCR-Pipeline repo)
assignment="${ASSIGNMENT_SCRIPT:-/path/to/Docker_with_bigstream_py/assignment.sh}"   # <- change to your path

files=($spots_registered/*spot*.csv)

if [ ${#files[@]} -gt 0 ]; then
    
    # Join the array elements into a comma-separated string
    file_list=$(IFS=, ; echo "${files[*]}")

else
    echo "no matching files found"
fi
# -s is segmentation image
# -v -v is relative voxel ratio, value multiplied to spots before assigning to segmentation file
    # if image is upscaled in z by 2, the spots need to be upscaled by 2 in z, so -v 1,1,2
# -o gene-by-cell matrix
# -p percent of spots assigned

mkdir -p "$step5dir"
"$assignment" \
    -s "$segmentation_tif" \
    -v 0.25,0.25,0.908 \
    -o "$step5dir/cell_by_transcript_matrix.csv" \
    -p "$step5dir/percent_spots_assigned.csv" \
    -i $file_list
