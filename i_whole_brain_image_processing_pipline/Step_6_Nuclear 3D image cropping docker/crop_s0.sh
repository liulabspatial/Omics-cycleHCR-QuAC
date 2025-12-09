#!/bin/bash

usage() {
	echo "Usage: crop_s0.sh [OPTION]... [FILE]"
	echo "cropping s0 level"
	echo
	echo "Options:"
    echo "  -o, --output		    path to an output directory"
    echo "  --step1		            output directory of step1"
    echo "  --step2		            output directory of step2, has subdirectory transform"
    echo "  --fix                   path to fix N5 used to perform registration in step2 (e.g. b0/t0)"
    echo "  --seg                   path to segmentation tiff from cellpose"
    echo "  --idx                   comma separated list of index"
	echo "  -h, --help		    display this help and exit"
	exit 1
}

for OPT in "$@"
do
	case "$OPT" in
		'-h'|'--help' )
			usage
			exit 1
			;;
		'-o'|'--output' )
			if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
				echo "$PROGNAME: option requires an argument -- $1" 1>&2
				exit 1
			fi
			outdir="$2"
			shift 2
			;;
        '--step1' )
			if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
				echo "$PROGNAME: option requires an argument -- $1" 1>&2
				exit 1
			fi
			step1dir="$2"
			shift 2
			;;
        '--step2' )
			if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
				echo "$PROGNAME: option requires an argument -- $1" 1>&2
				exit 1
			fi
			step2dir="$2"
			shift 2
			;;
        '--fix' )
			if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
				echo "$PROGNAME: option requires an argument -- $1" 1>&2
				exit 1
			fi
			fix_subpath="$2"
			shift 2
			;;
        '--seg' )
			if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
				echo "$PROGNAME: option requires an argument -- $1" 1>&2
				exit 1
			fi
			seg="$2"
			shift 2
			;;
        '--idx' )
			if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
				echo "$PROGNAME: option requires an argument -- $1" 1>&2
				exit 1
			fi
			idx="$2"
			shift 2
			;;
	esac
done

# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=$(dirname "$SCRIPT")
cd $SCRIPTPATH

# step1dir=output directory of step1
# step2dir=output directory of step2, has subdirectory transform
# fix=path to fix N5 used to perform registration in step2
# seg=path to segmentation tiff from cellpose
# idx=comma separated list of index
# outdir=outputdirectory where cropped tiff will be saved

#step1dir=/mnt/d/Docker_bigstream_spots/pipeline_mimic_pad/step1_multiTiles_pad
#step2dir=/mnt/d/Docker_bigstream_spots/pipeline_mimic_pad/step2_multitiles_pad
#fix=${step1dir}/${fix_subpath}
#seg=/mnt/d/Docker_bigstream_spots/pipeline_mimic_pad/step4_mimic/Mask_b0_t0_c3_s2.tiff
#idx=2000,4000
#outdir=/mnt/d/Docker_bigstream_spots/pipeline_mimic_pad/croptest2

fix=${step1dir}/${fix_subpath}

# loop through batch, loop through time, save as n5_arr
declare -a batch_arr=($(ls $step1dir))
declare -a mov_arr=()
for b in "${batch_arr[@]}"; do
    declare -a time_arr=($(ls "$step1dir"/"$b/" -I *mask.tif))
    for t in "${time_arr[@]}"; do
        n5=$(realpath "$step1dir"/"$b"/"$t")
        if [ "$n5" != "$(realpath $fix)" ]; then
            mov_arr+=("$n5")
        fi
    done
done
declare -p mov_arr


do_cropping_fix() {
    fix=$1
    seg=$2
    idx=$3
    out=$4

    singularity run \
        -B /home/liulab/labdata/Yumin/Bigstream_container/scripts:/scripts \
        -B "$fix":"$fix" \
        -B "$seg":"$seg" \
        -B "$out":"$out" \
        /home/liulab/labdata/Yumin/Bigstream_container/bigstream_open.sif \
        fix_segment_s0 \
        -f "$fix" \
        -seg "$seg" \
        -idx "$idx" \
        -o "$out"
}

export -f do_cropping_fix


export fix seg idx step2dir outdir


parallel --jobs 8 --verbose '
    singularity run \
        --bind /sys/fs/cgroup \
        --writable-tmpfs \
        --env TINI_SUBREAPER=true \
        -B /home/liulab/labdata/Yumin/Bigstream_container/scripts:/scripts \
        -B '"$fix"':'"$fix"' \
        -B {1}:{1} \
        -B '"$step2dir/transform"':'"$step2dir/transform"' \
        -B '"$seg"':'"$seg"' \
        -B '"$outdir"':'"$outdir"' \
        /home/liulab/labdata/Yumin/Bigstream_container/bigstream_open.sif \
        bigstream_segment_s0_parallel \
        -f '"$fix"' \
        -m {1} \
        -td '"$step2dir/transform"' \
        -seg '"$seg"' \
        -idx '"$idx"' \
        -o '"$outdir"'
' ::: "${mov_arr[@]}"