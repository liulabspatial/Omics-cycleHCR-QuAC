
inputpath="/home/liulab/labdata/wholebrain_output/Step1/"
outputpath="/home/liulab/labdata/wholebrain_output/Step2/"
fix="b3/t3"
dapi="c3"
res="s2"

/home/liulab/labdata/Yumin/scripts/bigstream_v2.sh \
	-i "$inputpath" \
	-o "$outputpath" \
	-f "$fix" \
	-d "$dapi" \
	-s "$res"
