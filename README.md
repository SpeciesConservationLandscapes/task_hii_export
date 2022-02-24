HII EXPORT TASK
---------------

This task exports the final [weightedsum](https://github.com/SpeciesConservationLandscapes/task_hii_weightedsum) 
product of Human Impact Index calculations for a given `taskdate` to a 
[Cloud Optimized GeoTIFF](https://www.cogeo.org/) (COG) in Google Cloud Storage (GCP). 
The initial Earth Engine export to COG 
[splits the TIFF](https://developers.google.com/earth-engine/guides/exporting#large-file-exports), 
so we download the parts, merge them with [GDAL](https://gdal.org/), and then re-export the final COG to GCP.

## Variables and Defaults

### Environment variables
```
SERVICE_ACCOUNT_KEY=<GOOGLE SERVICE ACCOUNT KEY>
```

### Class constants

```
scale=300
BUCKET = "hii-export"
NODATA = -32768  # to match .toInt16()
```

## Usage

*All parameters may be specified in the environment as well as the command line.*

```
/app # python task.py --help
usage: task.py [-h] [-d TASKDATE] [--overwrite]

optional arguments:
  -h, --help            show this help message and exit
  -d TASKDATE, --taskdate TASKDATE
  --overwrite           overwrite existing outputs instead of incrementing
```

### License
Copyright (C) 2022 Wildlife Conservation Society
The files in this repository  are part of the task framework for calculating 
Human Impact Index and Species Conservation Landscapes (https://github.com/SpeciesConservationLandscapes) 
and are released under the GPL license:
https://www.gnu.org/licenses/#GPL
See [LICENSE](./LICENSE) for details.
