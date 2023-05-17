import argparse
import ee
from osgeo import gdal
from osgeo.utils import gdal_merge as gm
from pathlib import Path
from task_base import HIITask


class HIIExport(HIITask):
    BUCKET = "hii-export"
    NODATA = -32768  # to match .toInt16()
    inputs = {
        "hii": {
            "ee_type": HIITask.IMAGECOLLECTION,
            "ee_path": "projects/HII/v1/hii",
            "maxage": 1,
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.noosm = kwargs.get("noosm", False)

    def calc(self):
        taskdate = self.taskdate.isoformat()
        localdir = f"/hii/{taskdate}"

        if self.noosm is False:
            self.hii, _ = self.get_most_recent_image(
                ee.ImageCollection(self.inputs["hii"]["ee_path"])
            )
            self.BUCKET = self.BUCKET
        else:
            self.hii, _ = self.get_most_recent_image(
                ee.ImageCollection(self.inputs["hii"]["ee_path"] + "_no_osm")
            )
            self.BUCKET = "hii-no-osm-export"

        self.image2storage(
            self.hii.unmask(self.NODATA).toInt16(), self.BUCKET, f"{taskdate}/hii"
        )
        self.wait()

        Path(localdir).mkdir(parents=True, exist_ok=True)

        # ee will write export from image2storage to multiple tiffs (for large images)
        tiffs = []
        for blob in self.gcsclient.list_blobs(self.BUCKET, prefix=taskdate):
            blob_path = blob.name
            local_path = f"{localdir}/{blob_path.split('/')[-1]}"
            self.download_from_cloudstorage(blob_path, local_path, self.BUCKET)
            tiffs.append(local_path)

        merge_args = [
            "",
            "-init",
            f"{self.NODATA}",
            "-a_nodata",
            f"{self.NODATA}",
            "-co",
            "COMPRESS=LZW",
            "-co",
            "NUM_THREADS=ALL_CPUS",
            "-co",
            "BIGTIFF=YES",
        ]
        merged_tiff = f"{localdir}/hii_{taskdate}_merged.tif"
        # TODO: replace with mosaic that doesn't write to disk
        gm.main(merge_args + ["-o", merged_tiff] + tiffs)

        cog = f"hii_{taskdate}.tif"
        local_cog = f"{localdir}/{cog}"
        blob_path = f"{taskdate}/{cog}"
        options = [
            "-of COG",
            "-co COMPRESS=LZW",
            "-co OVERVIEW_COMPRESS=WEBP",  # only available with GDAL 3.3+
        ]
        ds = gdal.Translate(local_cog, merged_tiff, options=" ".join(options))
        ds = None

        self.upload_to_cloudstorage(local_cog, blob_path, self.BUCKET)
        Path(merged_tiff).unlink(missing_ok=True)

    def check_inputs(self):
        super().check_inputs()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--taskdate")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite existing outputs instead of incrementing",
    )
    parser.add_argument(
        "-n",
        "--noosm",
        action="store_true",
        help="do not include osm in driver calculation",
    )
    options = parser.parse_args()
    hii_export_task = HIIExport(**vars(options))
    hii_export_task.run()
