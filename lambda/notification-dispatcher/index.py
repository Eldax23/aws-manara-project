"""
Notification Dispatcher Lambda Function
Publishes pipeline completion events and error alerts to Amazon SNS.
"""

import json
import logging
import os
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns_client = boto3.client('sns')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')


def handler(event, context):
    logger.info("Notification dispatcher invoked with event: %s", json.dumps(event))

    source_key = event.get('sourceKey', 'unknown')
    status = event.get('status', 'COMPLETED')
    variants = event.get('variants', {})
    meta = event.get('metadata', {})
    execution_id = event.get('executionId', 'unknown')

    subject = f"[AWS Image Pipeline] Image Processed Successfully: {os.path.basename(source_key)}"

    message_lines = [
        "AWS Serverless Image Processing Pipeline - Notification",
        "=" * 56,
        f"Status:             {status}",
        f"Source Asset:       {source_key}",
        f"Execution ID:       {execution_id}",
        f"Completed At:       {datetime.now(timezone.utc).isoformat()}",
        "",
        "Extracted Metadata:",
        f"  - Dimensions:     {meta.get('width', 'N/A')} x {meta.get('height', 'N/A')}",
        f"  - Aspect Ratio:   {meta.get('aspectRatio', 'N/A')}",
        f"  - Format:         {meta.get('format', 'N/A')}",
        f"  - MD5 Hash:       {meta.get('md5', 'N/A')}",
        "",
        "Generated Artifacts (Edge CDN / S3):"
    ]

    for variant_name, details in variants.items():
        message_lines.append(f"  • {variant_name.capitalize()}: {details.get('cdnUrl', details.get('key'))} ({details.get('sizeBytes', 0)} bytes)")

    message_body = "\n".join(message_lines)

    try:
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject[:100],
            Message=message_body,
            MessageAttributes={
                'PipelineStatus': {
                    'DataType': 'String',
                    'StringValue': status
                },
                'SourceKey': {
                    'DataType': 'String',
                    'StringValue': source_key
                }
            }
        )
        logger.info("Published SNS notification with messageId: %s", response.get('MessageId'))
        return {
            "statusCode": 200,
            "snsMessageId": response.get('MessageId')
        }
    except ClientError as e:
        logger.error("Failed to publish SNS notification: %s", str(e))
        return {
            "statusCode": 500,
            "error": str(e)
        }
