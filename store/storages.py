import os
import uuid

import cloudinary
from cloudinary import uploader, utils
from django.core.files.storage import Storage


class CloudinaryStorage(Storage):

    def _save(self, name, content):

        cloudinary.config(
            cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
            api_key=os.environ.get("CLOUDINARY_API_KEY"),
            api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
            secure=True
        )

        result = uploader.upload(
            content,
            public_id=str(uuid.uuid4()),
            folder="nexora",
            resource_type="image"
        )

        return result["public_id"]

    def _open(self, name, mode="rb"):
        raise NotImplementedError

    def exists(self, name):
        return False

    def delete(self, name):
        uploader.destroy(name, resource_type="image")

    def url(self, name):
        return utils.cloudinary_url(name, secure=True)[0]