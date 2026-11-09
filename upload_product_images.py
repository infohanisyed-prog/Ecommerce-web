import os
import django
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import cloudinary
from cloudinary import uploader
from django.conf import settings
from store.models import Product

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True,
)

for product in Product.objects.all():
    if not product.image:
        print(f"Skipped: {product.name} (no image)")
        continue

    image_path = Path(settings.MEDIA_ROOT) / product.image.name

    if not image_path.exists():
        print(f"File not found: {product.name}")
        continue

    result = uploader.upload(
        str(image_path),
        folder="nexora/products",
        public_id=image_path.stem,
        overwrite=True,
        resource_type="image",
    )

    product.image.name = result["public_id"]
    product.save(update_fields=["image"])

    print(f"Uploaded: {product.name}")

print("Image transfer completed!")