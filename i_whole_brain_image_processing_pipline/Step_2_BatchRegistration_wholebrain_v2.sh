
# === Configure these paths for your environment (or set as environment variables) ===
inputpath="${INPUT_PATH:-/path/to/wholebrain_output/Step1/}"   # <- change to your path
outputpath="${OUTPUT_PATH:-/path/to/wholebrain_output/Step2/}"   # <- change to your path
fix="b3/t3"
dapi="c3"
res="s2"
# Registration pipeline executable (from the CycleHCR-Pipeline repo)
bigstream="${BIGSTREAM_SCRIPT:-/path/to/scripts/bigstream_v2.sh}"   # <- change to your path

"$bigstream" \
	-i "$inputpath" \
	-o "$outputpath" \
	-f "$fix" \
	-d "$dapi" \
	-s "$res"
