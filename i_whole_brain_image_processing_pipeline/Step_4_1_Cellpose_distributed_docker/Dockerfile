# Use Miniforge as the base image
FROM condaforge/miniforge3
WORKDIR /app

RUN mamba create -n cellpose -c conda-forge python=3.10 \
    && mamba run -n cellpose pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu126 \
    && mamba run -n cellpose pip install git+https://github.com/mouseland/cellpose.git@15eb3c6 \
    && mamba run -n cellpose pip install zarr==2.18.3 dask-image==2026.5.0 \
    && mamba run -n cellpose conda install -y -c conda-forge dask=2026.6.0 dask-jobqueue=0.9.0 \
    && conda clean -afy \
    && mkdir -p /opt/conda/env/cellpose/etc/conda/activate.d \
    && echo "export TMPDIR=/tmp" > /opt/conda/env/cellpose/etc/conda/activate.d/env_vars.sh

COPY Cellpose_distributed.py .
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "/app/Cellpose_distributed.py"]

