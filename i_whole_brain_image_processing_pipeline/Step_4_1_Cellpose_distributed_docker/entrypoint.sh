#!/bin/bash
set -e

# Initialize conda
source /opt/conda/etc/profile.d/conda.sh

# Activate the cellpose environment
conda activate cellpose

# Run the command passed to the container (default: python Cellpose_distributed.py)
exec "$@"
