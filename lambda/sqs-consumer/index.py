"""
SQS Consumer Lambda Function
Processes S3 ObjectCreated events from SQS queue and triggers Step Functions State Machine.
"""

import json
import logging
import os
import urllib.parse
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sfn_client = boto3.client('stepfunctions')
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN', '')


def handler(event, context):
    """
    Consumes batch of SQS messages containing S3 event notifications.
    """
    logger.info("Received SQS event batch with %d records", len(event.get('Records', [])))
    results = []

    for record in event.get('Records', []):
        message_id = record.get('messageId', 'unknown')
        body_raw = record.get('body', '{}')

        try:
            body = json.loads(body_raw)
        except json.JSONDecodeError as err:
            logger.error("Failed to parse SQS body for message %s: %s", message_id, err)
            continue

        # Handle S3 Event Notification format
        s3_records = body.get('Records', [])
        if not s3_records:
            # Check if direct event
            if 's3' in body:
                s3_records = [body]

        for s3_event in s3_records:
            event_name = s3_event.get('eventName', '')
            if not event_name.startswith('ObjectCreated'):
                logger.info("Ignoring non-ObjectCreated event: %s", event_name)
                continue

            s3_data = s3_event.get('s3', {})
            bucket_name = s3_data.get('bucket', {}).get('name')
            raw_key = s3_data.get('object', {}).get('key', '')
            object_key = urllib.parse.unquote_plus(raw_key)
            object_size = s3_data.get('object', {}).get('size', 0)

            if not bucket_name or not object_key:
                logger.warning("Missing bucket or key in event: %s", json.dumps(s3_data))
                continue

            execution_input = {
                "sourceBucket": bucket_name,
                "sourceKey": object_key,
                "objectSize": object_size,
                "sqsMessageId": message_id,
                "triggeredAt": s3_event.get('eventTime', '')
            }

            # Generate sanitized execution name
            sanitized_key = "".join([c if c.isalnum() or c in "-_" else "_" for c in object_key])[:60]
            execution_name = f"exec-{sanitized_key}-{context.aws_request_id[:8]}"

            try:
                logger.info("Starting Step Functions execution '%s' for s3://%s/%s",
                            execution_name, bucket_name, object_key)
                response = sfn_client.start_execution(
                    stateMachineArn=STATE_MACHINE_ARN,
                    name=execution_name,
                    input=json.dumps(execution_input)
                )
                results.append({
                    "messageId": message_id,
                    "status": "STARTED",
                    "executionArn": response['executionArn']
                })
            except ClientError as e:
                logger.error("Failed to start Step Functions execution for %s: %s", object_key, str(e))
                raise e  # Raising triggers SQS retry / DLQ redrive

    return {
        "statusCode": 200,
        "processedCount": len(results),
        "results": results
    }
