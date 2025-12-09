spots_registered="/home/liulab/labdata/wholebrain_output/Step3/spots_filtered/"
segmentation_tif="/home/liulab/labdata/wholebrain_output/Step5/dilated_s3.tiff"
step5dir="/home/liulab/labdata/wholebrain_output/Step5/"

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
/home/liulab/labdata/Takashi/Docker_with_bigstream_py/assignment.sh \
    -s "/home/liulab/labdata/wholebrain_output/Step5/dilated_s3.tiff" \
    -v 0.25,0.25,0.908 \
    -o "$step5dir/cell_by_transcript_matrix.csv" \
    -p "$step5dir/percent_spots_assigned.csv" \
    -i $file_list
