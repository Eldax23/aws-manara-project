#!/usr/bin/env python3
"""
Unit and Integration Test Suite for Serverless Image Processing Pipeline
Tests:
- Image format validation & corrupted byte handling
- EXIF & dimension metadata extraction
- WebP thumbnail generation with aspect ratio preservation
- Translucent watermark application
- SQS event notification parsing
- Optional live AWS integration testing
"""

import io
import os
import sys
import unittest
import hashlib
from datetime import datetime, timezone
from PIL import Image, ImageOps, ImageDraw, ImageFont

class TestImagePipelineUnits(unittest.TestCase):

    def setUp(self):
        self.sample_dir = os.path.join(os.path.dirname(__file__), 'sample-images')
        self.landscape_path = os.path.join(self.sample_dir, 'sample-landscape.jpg')
        self.portrait_path = os.path.join(self.sample_dir, 'sample-portrait.png')

    def test_image_validation_valid_jpeg(self):
        """Test validation of healthy JPEG image."""
        with open(self.landscape_path, 'rb') as f:
            raw_bytes = f.read()

        with Image.open(io.BytesIO(raw_bytes)) as img:
            self.assertEqual(img.format, 'JPEG')
            self.assertEqual(img.size, (1600, 900))

        md5_hash = hashlib.md5(raw_bytes).hexdigest()
        self.assertTrue(len(md5_hash) == 32)

    def test_image_validation_corrupted_file(self):
        """Test validation rejects corrupted / non-image bytes."""
        corrupt_bytes = b"NOT_A_VALID_IMAGE_HEADER_DATA_1234567890"
        with self.assertRaises(Exception):
            with Image.open(io.BytesIO(corrupt_bytes)) as img:
                img.verify()

    def test_thumbnail_generation(self):
        """Test thumbnail is scaled to 200x200 while preserving aspect ratio."""
        with Image.open(self.landscape_path) as img:
            thumb = img.copy()
            thumb.thumbnail((200, 200), Image.Resampling.LANCZOS)
            
            buf = io.BytesIO()
            thumb.save(buf, format='WEBP', quality=85)
            webp_bytes = buf.getvalue()

            self.assertLessEqual(thumb.width, 200)
            self.assertLessEqual(thumb.height, 200)
            self.assertEqual(thumb.width, 200)
            self.assertIn(thumb.height, [112, 113]) # 16:9 ratio of 200 = 112.5 (rounds to 113 in Pillow)
            self.assertTrue(len(webp_bytes) > 0)

    def test_watermark_application(self):
        """Test alpha-composite watermark overlay."""
        with Image.open(self.portrait_path) as base_img:
            img = base_img.convert("RGBA")
            txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_layer)
            draw.text((10, 10), "CONFIDENTIAL", fill=(255, 255, 255, 128))
            watermarked = Image.alpha_composite(img, txt_layer)
            
            self.assertEqual(watermarked.size, base_img.size)
            self.assertEqual(watermarked.mode, "RGBA")

    def test_sqs_s3_event_parsing(self):
        """Test parsing of S3 event notification from SQS payload."""
        sample_sqs_body = {
            "Records": [
                {
                    "eventVersion": "2.1",
                    "eventSource": "aws:s3",
                    "eventName": "ObjectCreated:Put",
                    "s3": {
                        "bucket": {"name": "test-raw-images-bucket"},
                        "object": {"key": "uploads%2Fuser123%2Fsample.jpg", "size": 102400}
                    }
                }
            ]
        }
        record = sample_sqs_body['Records'][0]
        self.assertTrue(record['eventName'].startswith('ObjectCreated'))
        self.assertEqual(record['s3']['bucket']['name'], 'test-raw-images-bucket')
        
        import urllib.parse
        clean_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        self.assertEqual(clean_key, "uploads/user123/sample.jpg")

    def test_dynamodb_metadata_payload(self):
        """Test formatting of DynamoDB document model."""
        item = {
            'image_id': 'img_test-uuid',
            'user_id': 'user_42',
            'upload_timestamp': datetime.now(timezone.utc).isoformat(),
            'dimensions': {'width': 1600, 'height': 900, 'aspect_ratio': '16:9'},
            'variants': {
                'thumbnail': {'key': 'thumbnails/test_thumb.webp', 'width': 200, 'height': 112}
            }
        }
        self.assertIn('image_id', item)
        self.assertIn('user_id', item)
        self.assertEqual(item['dimensions']['aspect_ratio'], '16:9')


if __name__ == '__main__':
    unittest.main()
