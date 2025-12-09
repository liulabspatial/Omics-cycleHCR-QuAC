FROM condaforge/miniforge3

WORKDIR /app

RUN pip install --no-cache-dir \
    tifffile \
    pandas \
    numpy \
    anndata \
    scipy \
    scikit-image

COPY Pearson_correlation.py .

# docker build -t cell_measurement .