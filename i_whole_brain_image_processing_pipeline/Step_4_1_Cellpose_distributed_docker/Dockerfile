# Use Miniforge as the base image
FROM condaforge/miniforge3

WORKDIR /app

#RUN conda env create -f environment.yml && conda clean -afy

RUN mamba create -n cellpose -c conda-forge python=3.10 \
    && mamba run -n cellpose pip uninstall torch \
    && mamba run -n cellpose pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126 \
    && mamba run -n cellpose pip install git+https://www.github.com/mouseland/cellpose.git \
    && mamba run -n cellpose pip install zarr \
    && mamba run -n cellpose conda install dask \
    && mamba run -n cellpose python -m pip install dask-image \
    && mamba run -n cellpose conda install dask-jobqueue -c conda-forge \
    && conda clean -afy \
    && mkdir -p /opt/conda/env/cellpose/etc/conda/activate.d \
    && echo "export TMPDIR=/tmp" > /opt/conda/env/cellpose/etc/conda/activate.d/env_vars.sh


COPY Cellpose_distributed.py .
COPY entrypoint.sh .
COPY fix_b1_t3_c3_s2_z4_412-hippo.tif .