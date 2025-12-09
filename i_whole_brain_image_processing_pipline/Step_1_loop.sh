inputpath="/home/liulab/labdata/wholebrain/"
outputpath="/home/liulab/labdata/wholebrain_output/Step1/"


# Check if the directory exists
if [ ! -d "$outputpath" ]; then
    # The directory does not exist, create it
    mkdir -p "$outputpath"
    echo "Directory created: $outputpath"
else
    echo "Directory already exists: $outputpath"
fi



prefix="b*"
declare -a batches=("${inputpath}"${prefix})

for b in "${batches[@]}"; do
    batch=$(basename "$b")
    batch_input=$(realpath "$inputpath/$batch/")
    batch_output=$(realpath "$outputpath/$batch/")

    # Specify the directory to check
    dir=$batch_output

    # Check if the directory exists
    if [ ! -d "$dir" ]; then
        # The directory does not exist, create it
        mkdir -p "$dir"
        echo "Directory created: $dir"
    else
        echo "Directory already exists: $dir"
    fi

    # Setting the suffix and populating the array with filenames
    suffix=".nd2"
    files=("${batch_input}"/*${suffix})

    # Initialize the counter
    i=0

    # Process each file

    for file in "${files[@]}"
    do
        outputdir="${batch_output}/t${i}"  # Construct the output directory name
        checkpoint="$(basename "$file" "$suffix").checkpoint"
        file_cp="$outputdir/$checkpoint"

        ((i++))  # Increment the counter
        if [ -f $file_cp ]; then
            echo "checkpoint: $file_cp ::: exists"
        else
            echo "Processing $file ::: Output will be in $outputdir"
            /home/liulab/labdata/nf/ND2-Stitching-Pipeline/nd2n5.sh \
                    -i $file \
                    -o $outputdir \
                    -t 120 -c 200 -c2 200 -d 3 \
                    --skipDeform \
                    --oneTileWins
        fi
    done

done
