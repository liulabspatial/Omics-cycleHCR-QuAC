----------------Build Docker---------------

# start docker from Start menu
# open terminal in the current folder

docker build -t bigstream .

----------------Run in Docker---------------

# The container dispatches by script name:
#   docker run bigstream <script_name> <args>
# runs  python /app/<script_name>.py <args>
# (see crop_s0.sh for the full argument list, e.g. -f -m -td -seg -idx -o)

docker run bigstream bigstream_segment_s0_parallel <args>

# Or open an interactive shell for testing:

docker run -it --entrypoint /bin/bash bigstream
conda activate myenv
cd /app
# run image cropping script by
python bigstream_segment_s0_parallel.py <args>



--------------Build Singularity container------------------

## Export docker to Singularity

# In a new terminal
docker save bigstream -o bigstream.tar

singularity build bigstream_open.sif docker-archive://./bigstream.tar

-----------------Run in Singularity-----------------------

# fill in all input/output folder information, and list of selected cells' indexes in crop_open.sh

# In the directory of crop_open.sh

bash crop_open.sh

