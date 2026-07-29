#!/bin/bash
set -e

# Initialize conda
source /opt/conda/etc/profile.d/conda.sh

# Activate your environment
conda activate cellpose

# Run the command passed to the container
exec "$@"