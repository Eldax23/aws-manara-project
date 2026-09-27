"""
Presigned URL Generator Lambda Function
Generates short-lived, cryptographically signed S3 PUT URLs for direct client uploads.
"""

import json
import logging
import os
import uuid
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

SOURCE_BUCKET = os.environ.get('SOURCE_BUCKET', '')
URL_EXPIRATION = int(os.environ.get('URL_EXPIRATION_SECONDS', '900'))  # Default 15 minutes
MAX_FILE_SIZE_MB = int(os.environ.get('MAX_FILE_SIZE_MB', '15'))

ALLOWED_CONTENT_TYPES = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/webp': '.webp',
    'image/gif': '.gif',
}

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key',
    'Access-Control-Allow-Methods': 'GET,OPTIONS'
}


def handler(event, context):
    logger.info("Received event: %s", json.dumps(event))

    http_method = event.get('httpMethod', '')
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({'message': 'CORS preflight successful'})
        }

    query_params = event.get('queryStringParameters') or {}
    filename = query_params.get('filename', 'upload.jpg')
    content_type = query_params.get('contentType', 'image/jpeg').lower()
    user_id = query_params.get('userId', 'anonymous')

    if content_type not in ALLOWED_CONTENT_TYPES:
        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'error': f'Unsupported content-type: {content_type}. Allowed: {list(ALLOWED_CONTENT_TYPES.keys())}'
            })
        }

    ext = ALLOWED_CONTENT_TYPES[content_type]
    unique_id = str(uuid.uuid4())
    object_key = f"uploads/{user_id}/{unique_id}{ext}"

    try:
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': SOURCE_BUCKET,
                'Key': object_key,
                'ContentType': content_type,
                'Metadata': {
                    'original-filename': filename,
                    'user-id': user_id,
                    'upload-id': unique_id
                }
            },
            ExpiresIn=URL_EXPIRATION
        )

        logger.info("Generated presigned URL for key: %s in bucket: %s", object_key, SOURCE_BUCKET)

        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'uploadUrl': presigned_url,
                'bucket': SOURCE_BUCKET,
                'key': object_key,
                'fileId': unique_id,
                'expiresInSeconds': URL_EXPIRATION,
                'maxSizeMB': MAX_FILE_SIZE_MB,
                'instructions': 'Send a PUT request with your binary file to uploadUrl with Content-Type header matching contentType'
            })
        }

    except ClientError as e:
        logger.error("Error generating presigned URL: %s", str(e))
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Failed to generate pre-signed upload URL'})
        }
