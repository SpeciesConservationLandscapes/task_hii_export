import argparse
import ee
from google.cloud.storage import Client
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
        self.gclient = Client()

        self.hii, _ = self.get_most_recent_image(
            ee.ImageCollection(self.inputs["hii"]["ee_path"])
        )

    # TODO: refactor into task_base
    def download_from_cloudstorage(self, blob_path: str, local_path: str) -> str:
        bucket = self.gclient.get_bucket(self.BUCKET)
        blob = bucket.blob(blob_path)
        blob.download_to_filename(local_path)
        return local_path

    def upload_to_cloudstorage(self, local_path: str, blob_path: str) -> str:
        bucket = self.gclient.get_bucket(self.BUCKET)
        blob = bucket.blob(blob_path)
        blob.upload_from_filename(local_path, timeout=3600)
        return blob_path

    def calc(self):
        taskdate = self.taskdate.isoformat()
        prefix = f"hii/{taskdate}"

        self.export_image_cloudstorage(
            self.hii.unmask(self.NODATA).toInt16(), self.BUCKET, f"{prefix}/hii"
        )
        self.wait()
        Path(f"/{prefix}").mkdir(parents=True, exist_ok=True)

        tiffs = []
        for blob in self.gclient.list_blobs(self.BUCKET, prefix=prefix):
            blob_path = blob.name
            local_path = f"/{prefix}/{blob_path.split('/')[-1]}"
            self.download_from_cloudstorage(blob_path, local_path)
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
        merged_tiff = f"/{prefix}/hii_{taskdate}_merged.tif"
        # TODO: replace with mosaic that doesn't write to disk
        gm.main(merge_args + ["-o", merged_tiff] + tiffs)

        blob_path = f"{prefix}/hii_{taskdate}.tif"
        cog = f"/{blob_path}"
        options = "-of COG -co COMPRESS=LZW"
        ds = gdal.Translate(cog, merged_tiff, options=options)
        ds = None

        self.upload_to_cloudstorage(cog, blob_path)
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
    options = parser.parse_args()
    hii_export_task = HIIExport(**vars(options))
    hii_export_task.run()
