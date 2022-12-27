FROM scl3/task_base:latest

RUN apt-get update
RUN apt-get install -y gdal-bin libgdal-dev g++

RUN pip uninstall -y gdal
RUN pip install --no-cache-dir numpy==1.21.4
RUN pip install GDAL==$(gdal-config --version) --global-option=build_ext --global-option="-I/usr/include/gdal"
RUN pip install --no-cache-dir git+https://github.com/SpeciesConservationLandscapes/task_base.git

WORKDIR /app
COPY $PWD/src .
