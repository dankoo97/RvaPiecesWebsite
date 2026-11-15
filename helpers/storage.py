from urllib.parse import quote

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class CloudReadStorage(FileSystemStorage):
    """
    Local development storage that reads media from the production bucket.

    - Files that exist locally (e.g. something you just uploaded) are served from MEDIA_URL.
    - Files that don't exist locally are served from the public cloud bucket URL.
    - All writes/deletes stay on the local filesystem, so the production bucket is never modified.
    """

    def __init__(self, *args, bucket_url=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.bucket_url = (bucket_url or settings.CLOUD_READ_BUCKET_URL).rstrip(
            "/"
        ) + "/"

    def url(self, name):
        if name and not self.exists(name):
            return self.bucket_url + quote(str(name).replace("\\", "/").lstrip("/"))
        return super().url(name)
