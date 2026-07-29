FROM condaforge/miniforge3

WORKDIR /app

RUN pip install --no-cache-dir \
    tifffile \
    pandas \
    numpy \
    anndata \
    scipy \
    scikit-image

COPY Step_12_write_ML_image_dataset.py .
COPY Step_7_measure_nucleus_intensity.py .

# docker build -t cell_measurement .