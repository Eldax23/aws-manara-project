"""
Image Processor Lambda Function
Orchestrated by AWS Step Functions tasks:
1. validate_image
2. extract_metadata
3. resize_and_watermark
4. persist_and_catalog
"""

import io
import json
import logging
import os
import hashlib
import time
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError
from PIL import Image, ImageDraw, ImageFont, ImageOps

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

DESTINATION_BUCKET = os.environ.get('DESTINATION_BUCKET', '')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', '')
CLOUDFRONT_DOMAIN = os.environ.get('CLOUDFRONT_DOMAIN', '')
WATERMARK_TEXT = os.environ.get('WATERMARK_TEXT', 'PROCESSED')
MAX_FILE_SIZE_BYTES = int(os.environ.get('MAX_FILE_SIZE_MB', '15')) * 1024 * 1024


def get_s3_image(bucket: str, key: str) -> bytes:
    """Download image bytes from S3."""
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return response['Body'].read()


def task_validate(event: dict) -> dict:
    """Validates image size, format, and magic bytes."""
    bucket = event['sourceBucket']
    key = event['sourceKey']
    size = event.get('objectSize', 0)

    logger.info("Validating image: s3://%s/%s (reported size: %d bytes)", bucket, key, size)

    # Check file size limit
    if size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File size {size} bytes exceeds maximum allowed limit {MAX_FILE_SIZE_BYTES} bytes")

    image_bytes = get_s3_image(bucket, key)
    actual_size = len(image_bytes)

    if actual_size == 0:
        raise ValueError("Uploaded file is empty (0 bytes)")

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img_format = img.format.upper() if img.format else "UNKNOWN"
            if img_format not in ["JPEG", "PNG", "WEBP", "GIF"]:
                raise ValueError(f"Unsupported image format '{img_format}'. Must be JPEG, PNG, or WEBP.")
            width, height = img.size
    except Exception as e:
        logger.error("Image verification failed for %s: %s", key, str(e))
        raise ValueError(f"Invalid or corrupted image file: {str(e)}")

    md5_hash = hashlib.md5(image_bytes).hexdigest()

    return {
        "status": "VALIDATED",
        "format": img_format,
        "width": width,
        "height": height,
        "byteSize": actual_size,
        "md5Checksum": md5_hash
    }


def task_extract_metadata(event: dict) -> dict:
    """Extracts detailed technical metadata, aspect ratio, and color channels."""
    bucket = event['sourceBucket']
    key = event['sourceKey']
    val_info = event.get('validation', {})

    width = val_info.get('width', 0)
    height = val_info.get('height', 0)
    gcd_val = math_gcd(width, height) if width and height else 1
    aspect_ratio = f"{width // gcd_val}:{height // gcd_val}" if gcd_val > 0 else "1:1"

    image_bytes = get_s3_image(bucket, key)
    with Image.open(io.BytesIO(image_bytes)) as img:
        color_mode = img.mode
        has_alpha = color_mode in ('RGBA', 'LA') or ('transparency' in img.info)

    metadata = {
        "width": width,
        "height": height,
        "aspectRatio": aspect_ratio,
        "colorMode": color_mode,
        "hasAlphaChannel": has_alpha,
        "format": val_info.get('format', 'UNKNOWN'),
        "md5": val_info.get('md5Checksum', ''),
        "extractedAt": datetime.now(timezone.utc).isoformat()
    }

    return metadata


def math_gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def create_watermarked_image(base_img: Image.Image, text: str) -> Image.Image:
    """Applies a subtle, semi-transparent watermark text across the image."""
    img = base_img.convert("RGBA")
    txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    w, h = img.size
    font_size = max(16, int(h * 0.04))
    font = ImageFont.load_default()

    watermark_str = f" {text}  |  {datetime.now(timezone.utc).strftime('%Y-%m-%d')} "
    bbox = draw.textbbox((0, 0), watermark_str, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Position at bottom-right with margin
    x = w - tw - 20
    y = h - th - 20

    # Draw shadow and translucent text
    draw.text((x + 1, y + 1), watermark_str, fill=(0, 0, 0, 100), font=font)
    draw.text((x, y), watermark_str, fill=(255, 255, 255, 140), font=font)

    watermarked = Image.alpha_composite(img, txt_layer)
    return watermarked.convert("RGB")


def task_resize_and_watermark(event: dict) -> dict:
    """Generates thumbnail (200x200) and watermarked preview (600x600) in WebP format."""
    bucket = event['sourceBucket']
    key = event['sourceKey']
    base_name = os.path.splitext(os.path.basename(key))[0]

    image_bytes = get_s3_image(bucket, key)
    dest_bucket = DESTINATION_BUCKET

    variants = {}

    with Image.open(io.BytesIO(image_bytes)) as original_img:
        # Normalize orientation using EXIF if present
        img = ImageOps.exif_transpose(original_img) or original_img

        # 1. Generate Thumbnail (200x200 aspect-ratio preserved)
        thumb = img.copy()
        thumb.thumbnail((200, 200), Image.Resampling.LANCZOS)
        thumb_buf = io.BytesIO()
        thumb.save(thumb_buf, format='WEBP', quality=85, method=6)
        thumb_bytes = thumb_buf.getvalue()

        thumb_key = f"thumbnails/{base_name}_thumb.webp"
        s3_client.put_object(
            Bucket=dest_bucket,
            Key=thumb_key,
            Body=thumb_bytes,
            ContentType='image/webp',
            CacheControl='public, max-age=31536000, immutable'
        )
        variants['thumbnail'] = {
            'key': thumb_key,
            'width': thumb.width,
            'height': thumb.height,
            'sizeBytes': len(thumb_bytes),
            'cdnUrl': f"https://{CLOUDFRONT_DOMAIN}/{thumb_key}" if CLOUDFRONT_DOMAIN else f"s3://{dest_bucket}/{thumb_key}"
        }

        # 2. Generate Watermarked Preview (600x600 max)
        preview = img.copy()
        preview.thumbnail((800, 800), Image.Resampling.LANCZOS)
        watermarked_preview = create_watermarked_image(preview, WATERMARK_TEXT)
        preview_buf = io.BytesIO()
        watermarked_preview.save(preview_buf, format='WEBP', quality=85, method=6)
        preview_bytes = preview_buf.getvalue()

        preview_key = f"previews/{base_name}_wm.webp"
        s3_client.put_object(
            Bucket=dest_bucket,
            Key=preview_key,
            Body=preview_bytes,
            ContentType='image/webp',
            CacheControl='public, max-age=31536000, immutable'
        )
        variants['preview'] = {
            'key': preview_key,
            'width': watermarked_preview.width,
            'height': watermarked_preview.height,
            'sizeBytes': len(preview_bytes),
            'cdnUrl': f"https://{CLOUDFRONT_DOMAIN}/{preview_key}" if CLOUDFRONT_DOMAIN else f"s3://{dest_bucket}/{preview_key}"
        }

    return variants


def task_persist_and_catalog(event: dict) -> dict:
    """Saves complete execution record into DynamoDB."""
    table = dynamodb.Table(DYNAMODB_TABLE)
    key = event['sourceKey']
    base_name = os.path.splitext(os.path.basename(key))[0]

    image_id = f"img_{base_name}"
    user_id = key.split('/')[1] if 'uploads/' in key and len(key.split('/')) > 2 else "anonymous"
    now_iso = datetime.now(timezone.utc).isoformat()

    item = {
        'image_id': image_id,
        'user_id': user_id,
        'source_bucket': event['sourceBucket'],
        'source_key': event['sourceKey'],
        'destination_bucket': DESTINATION_BUCKET,
        'upload_timestamp': now_iso,
        'processing_status': 'COMPLETED',
        'metadata': event.get('metadata', {}),
        'variants': event.get('variants', {}),
        'execution_id': event.get('executionId', 'unknown')
    }

    try:
        table.put_item(Item=item)
        logger.info("Successfully persisted image metadata to DynamoDB table %s for image_id %s",
                    DYNAMODB_TABLE, image_id)
    except ClientError as e:
        logger.error("Failed to write item to DynamoDB: %s", str(e))
        raise e

    return {
        "status": "CATALOGED",
        "imageId": image_id,
        "persistedAt": now_iso,
        "item": item
    }


def handler(event, context):
    """
    Dispatcher based on Step Functions Task action.
    """
    logger.info("Image processor invoked with event: %s", json.dumps(event))
    action = event.get('action')

    if action == 'validate':
        return task_validate(event)
    elif action == 'extract_metadata':
        return task_extract_metadata(event)
    elif action == 'resize_and_watermark':
        return task_resize_and_watermark(event)
    elif action == 'persist_and_catalog':
        return task_persist_and_catalog(event)
    else:
        # Default full pipeline execution if invoked directly
        val = task_validate(event)
        event['validation'] = val
        meta = task_extract_metadata(event)
        event['metadata'] = meta
        variants = task_resize_and_watermark(event)
        event['variants'] = variants
        catalog = task_persist_and_catalog(event)
        return {
            "validation": val,
            "metadata": meta,
            "variants": variants,
            "catalog": catalog
        }
