----------------Build Docker---------------

# start docker from Start menu
# open terminal in the current folder

docker build -t bigstream .

----------------Run in Docker---------------

docker run -it bigstream

conda activate myenv

cd scripts/

# run image cropping script by
python bigstream_segment_s0_local.py



--------------Build Singularity container------------------

## Export docker to Singularity

# In a new terminal
docker save bigstream -o bigstream.tar

singularity build bigstream_open.sif docker-archive://./bigstream.tar

-----------------Run in Singularity-----------------------

# fill in all input/output folder information, and list of selected cells' indexes in crop_open.sh

# In the directory of crop_open.sh

bash crop_open.sh

