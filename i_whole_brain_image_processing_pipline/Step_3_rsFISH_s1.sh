
# list of inputs
# step1dir
# step2dir
# step3dir
# rsfish param

# loop through batch, loop through time, save as n5_arr

step1dir=/home/liulab/labdata/wholebrain_output/Step1/
step2dir=/home/liulab/labdata/wholebrain_output/Step2/
step3dir=/home/liulab/labdata/wholebrain_output/Step3/
dapi=c3
rsparam="--rsfish_gb_per_core 8 --rsfish_min 0 --rsfish_max 600 --rsfish_anisotropy 1.0 --rsfish_sigma 1.18 --rsfish_ransac 0 --rsfish_threshold 0.00353 --rsfish_background 0 --rsfish_intensity 0"



declare -a batch_arr=($(ls $step1dir))
declare -a n5_arr=()
for b in "${batch_arr[@]}"; do
    declare -a time_arr=($(ls "$step1dir"/"$b/" -I *mask.tif -I *.checkpoint))
    for t in "${time_arr[@]}"; do
        n5=$(realpath "$step1dir"/"$b"/"$t")
        n5_arr+=("$n5")
    done
done
declare -p n5_arr

do_warp_spots() {
	local n5=$(realpath $1)
	local transformdir=$(realpath $2/transform)
	local spotsdir=$(realpath $3)/spots
	local warpdir=$(realpath $3)/spots_registered
	local dapi=$4
	local rsparam=$5
#	echo "$n5"
#	echo "$transformdir"
#	echo "$spotsdir"
#	echo "$warpdir"
#	echo "\"$rsparam\""

		if [ -d "$n5/.nextflow" ]; then
		rm -r "$n5"/.nextflow
	fi
	if [ -d "$n5/work" ]; then
		rm -r "$n5"/work
	fi
	for dir in "$n5"/tmp*; do
		echo "tmp"
		if [ -d "$dir" ]; then
			rm -rf "$dir"
		fi
	done

	/home/liulab/labdata/nf/RSFISH-WarpSpots/rs_warp_Yumin.sh \
		-i "$n5" \
		-o "$warpdir" \
		-r "$spotsdir" \
		-x "$transformdir" \
		-w 40 -d "$dapi" -s s1 \
		-- "$rsparam"

}

export -f do_warp_spots

for n in "${n5_arr[@]}"; do
	do_warp_spots "$n" "$step2dir" "$step3dir" "$dapi" "$rsparam"
done


