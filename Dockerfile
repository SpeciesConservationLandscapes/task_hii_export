FROM scl3/task_base:latest

RUN apt-get update
RUN apt-get install -y gdal-bin libgdal-dev g++

RUN /usr/local/bin/python -m pip install --no-cache-dir \
    gdal==3.2.2 \
    git+https://github.com/SpeciesConservationLandscapes/task_base.git

WORKDIR /app
COPY $PWD/src .
