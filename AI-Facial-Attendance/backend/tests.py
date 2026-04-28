from io import BytesIO

import numpy as np
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from faceapp.views import _load_face_image


class LoadFaceImageTests(SimpleTestCase):
    def _build_upload(self, mode="RGB", image_format="PNG", size=(8, 8), color=None):
        color = color or ((10, 20, 30) if mode in {"RGB", "RGBA"} else 120)
        image = Image.new(mode, size, color=color)
        buffer = BytesIO()
        image.save(buffer, format=image_format)
        return SimpleUploadedFile(
            name=f"face.{image_format.lower()}",
            content=buffer.getvalue(),
            content_type=f"image/{image_format.lower()}",
        )

    def test_load_face_image_returns_rgb_uint8_array_for_png_upload(self):
        image_file = self._build_upload(mode="RGBA", image_format="PNG", color=(10, 20, 30, 255))

        normalized_image, image_array = _load_face_image(image_file)

        self.assertEqual(normalized_image.mode, "RGB")
        self.assertEqual(image_array.dtype, np.uint8)
        self.assertEqual(image_array.shape, (8, 8, 3))
        self.assertTrue(image_array.flags.c_contiguous)
        self.assertListEqual(image_array[0, 0].tolist(), [10, 20, 30])
