FROM condaforge/mambaforge as builder

# create conda environment, python 3.11+ is needed for new bigstream
# install bigstream by pip


# deals with interactive prompt
ENV DEBIAN_FRONTEND noninteractive

# install global packages
RUN apt-get update -y \
    && apt-get install -y libgl1 \
    && apt-get install -y libglib2.0-0

# set up conda environment and install bigstream
RUN mamba create -n myenv -c conda-forge python=3.11 \
    && mamba run -n myenv pip install bigstream==1.4.1 \
    && mamba run -n myenv pip install pandas \

    && mamba clean --tarballs -y \
    && mkdir -p /opt/conda/env/myenv/etc/conda/activate.d \
    && echo "export TMPDIR=/tmp" > /opt/conda/env/myenv/etc/conda/activate.d/env_vars.sh

COPY scripts /app


# make a bash script entrypoint.sh that calls specific python scripts
RUN echo "#!/bin/bash" >> /entrypoint.sh \
    && echo "source /opt/conda/etc/profile.d/conda.sh" >> /entrypoint.sh \
    && echo "SCRIPT_NAME=\$1; shift" >> /entrypoint.sh \
    && echo "conda activate myenv" >> /entrypoint.sh \
    && echo 'python /app/${SCRIPT_NAME}.py "$@"' >> /entrypoint.sh \
    && chmod +x /entrypoint.sh


