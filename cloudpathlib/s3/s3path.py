import os
from pathlib import Path
from tempfile import TemporaryDirectory

from ..cloudpath import CloudPath, register_path_class


@register_path_class("s3")
class S3Path(CloudPath):
    cloud_prefix: str = "s3://"

    @property
    def drive(self) -> str:
        return self.bucket

    def is_dir(self) -> bool:
        return self.client._is_file_or_dir(self) == "dir"

    def is_file(self) -> bool:
        return self.client._is_file_or_dir(self) == "file"

    def mkdir(self, parents=False, exist_ok=False):
        # not possible to make empty directory on s3
        pass

    def touch(self):
        if self.exists():
            self.client._move_file(self, self)
        else:
            tf = TemporaryDirectory()
            p = Path(tf.name) / "empty"
            p.touch()

            self.client._upload_file(p, self)

            tf.cleanup()

    def stat(self):
        meta = self.client._get_metadata(self)

        return os.stat_result(
            (
                None,  # mode
                None,  # ino
                self.cloud_prefix,  # dev,
                None,  # nlink,
                None,  # uid,
                None,  # gid,
                meta.get("size", 0),  # size,
                None,  # atime,
                meta.get("last_modified", 0).timestamp(),  # mtime,
                None,  # ctime,
            )
        )

    @property
    def bucket(self) -> str:
        return self._no_prefix.split("/", 1)[0]

    @property
    def key(self) -> str:
        key = self._no_prefix_no_drive

        # key should never have starting slash for
        # use with boto, etc.
        if key.startswith("/"):
            key = key[1:]

        return key

    @property
    def etag(self):
        return self.client._get_metadata(self).get("etag")
