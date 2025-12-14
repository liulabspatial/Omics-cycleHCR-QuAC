#!/bin/bash

usage() {
	echo "Usage: bigstream.sh [OPTION]... [FILE]"
	echo "Bigstream in memory"
	echo
	echo "Options:"
	echo "  -i, --input		    path to a step1 directory"
        echo "  -o, --output		    path to a step2 directory"
        echo "  -f, --fix		    subpath to fix n5, e.g b0/t0"
        echo "  -d, --dapi		    DAPI channel, e.g c3"
        echo "  -s, --res		    resolution of registration, e.g s2"
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
		'-i'|'--input' )
			if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
				echo "$PROGNAME: option requires an argument -- $1" 1>&2
				exit 1
			fi
			INPUT="$2"
			shift 2
			;;
		'-o'|'--output' )
			if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
				echo "$PROGNAME: option requires an argument -- $1" 1>&2
				exit 1
			fi
			OUTPUT="$2"
			shift 2
			;;
                '-f'|'--fix' )
                        if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                                exit 1
                        fi
                        FIX="$2"
                        shift 2
                        ;;
                '-d'|'--dapi' )
                        if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                                exit 1
                        fi
                        DAPI="$2"
                        shift 2
                        ;;
                '-s'|'--resolution' )
                        if [[ -z "$2" ]] || [[ "$2" =~ ^-+ ]]; then
                                echo "$PROGNAME: option requires an argument -- $1" 1>&2
                                exit 1
                        fi
                        RES="$2"
                        shift 2
                        ;;
	esac
done

# specify 3 things: directory of step1 (stitching), specify fix N5, specify output directory of below process, step2 (registration) #

step1outdir=${INPUT}
fix="$step1outdir"/${FIX}
step2outdir=${OUTPUT}
dapi=${DAPI}
res=${RES}

echo "$step1outdir"
echo "$fix"
echo "$step2outdir"
echo "$dapi"
echo "$res"


if [ ! -d "$step2outdir" ]; then
    mkdir -p "$step2outdir"
    echo "Directory created: $step2outdir"
else
    echo "Directory already exists: $step2outdir"
fi

# loop through batch, loop through time, save as mov_arr except for fix n5
declare -a batch_arr=($(ls $step1outdir))
declare -a mov_arr=()
for b in "${batch_arr[@]}"; do
    declare -a time_arr=($(ls "$step1outdir"/"$b/" -I *mask.tif -I *.checkpoint))
    for t in "${time_arr[@]}"; do
        n5=$(realpath "$step1outdir"/"$b"/"$t")
        if [ "$n5" != "$(realpath $fix)" ]; then
            mov_arr+=("$n5")
        fi
    done
done
declare -p mov_arr

# make a function that runs singularity, and takes three inputs: fix, mov, output
do_bigstream() {
    fix=$1
    mov=$2
    out=$3
    dapi=$4
    res=$5

    # get path of mask.tif from fix/mov path
    fix_mask="$(dirname $fix)/$(basename $fix)_mask.tif"
    mov_mask="$(dirname $mov)/$(basename $mov)_mask.tif"

    singularity run \
            --env TINI_SUBREAPER=true \
            -B "$fix":"$fix" \
            -B "$mov":"$mov" \
            -B "$out":"$out" \
            -B "$fix_mask":"$fix_mask" \
            -B "$mov_mask":"$mov_mask" \
	    /home/liulab/labdata/Takashi/Docker_with_bigstream_py/bigstream-py-0.0.12.sif \
            /entrypoint.sh bigstream_in_memory \
            -f "$fix" \
            -m "$mov" \
            --fix_mask "$fix_mask" \
            --mov_mask "$mov_mask" \
            -s "$res" \
            -d "$dapi" \
            -o "$out" \
            --aff_as 2 \
            --aff_sf 2,1 \
            --aff_ss 2,0.25 \
            --aff_n 500 \
            --def_as 2 \
            --def_sf 2 \
            --def_ss 0.5 \
            --def_n 10 \
            --def_cps 128 \
            --deform 0

            
}
export -f do_bigstream

############# fix N5 to tiff ##################
singularity run \
        --env TINI_SUBREAPER=true \
        -B "$fix":"$fix" \
        -B "$step2outdir":"$step2outdir" \
	/home/liulab/labdata/Takashi/Docker_with_bigstream_py/bigstream-py-0.0.12.sif \
        /entrypoint.sh fix_n5tiff \
        -f "$fix" \
        -o "$step2outdir" \
        -s "$res"

############ parallel registration over mov_arr ###############
# fix and output directory doesn't change #
parallel --jobs=3 --verbose do_bigstream ::: "$fix" ::: ${mov_arr[@]} ::: "$step2outdir" ::: "$dapi" ::: "$res"
