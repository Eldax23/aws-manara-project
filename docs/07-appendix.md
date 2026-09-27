# 7. Appendix & Operational Runbooks

## 7.1 AWS Service Inventory

| AWS Service | Resource / Logical Name | Purpose in Architecture |
|---|---|---|
| **Amazon S3** | `RawImagesSourceBucket` | Ingests uncompressed raw image uploads directly from clients via pre-signed URLs. |
| **Amazon S3** | `ProcessedImagesDestBucket` | Stores generated WebP thumbnails, previews, and watermarked outputs. |
| **Amazon S3** | `CloudFrontAccessLogsBucket` | Captures access logs from CloudFront edge distributions for auditing. |
| **Amazon SQS** | `ImageProcessingQueue` | Standard message queue buffering S3 `ObjectCreated` event notifications. |
| **Amazon SQS** | `ImageProcessingDLQ` | Dead-Letter Queue storing messages that repeatedly fail processing (`maxReceiveCount = 3`). |
| **AWS Lambda** | `PresignedUrlGeneratorFunction` | Generates secure, short-lived S3 PUT URLs with file-type enforcement. |
| **AWS Lambda** | `SQSConsumerFunction` | Consumes messages from SQS and launches Step Functions executions. |
| **AWS Lambda** | `ImageProcessorFunction` | Executes validation, EXIF metadata extraction, thumbnail resizing, and watermarking using Pillow. |
| **AWS Step Functions**| `ImageProcessingWorkflow` | Visual state machine coordinating the multi-step transformation sequence. |
| **Amazon DynamoDB**| `ImageMetadataTable` | Stores structured metadata, dimensions, hashes, and CDN variant links. |
| **Amazon CloudFront**| `ProcessedImagesDistribution` | High-speed global content delivery network fronting the processed images S3 bucket. |
| **Amazon SNS** | `ImageProcessingAlertsTopic` | Publishes real-time notification alerts on pipeline completion and DLQ alarms. |
| **Amazon CloudWatch**| `ImageProcessingDLQAlarm` | Alarms when messages appear in the Dead-Letter Queue. |
| **Amazon API Gateway**| `ImageUploadRestApi` | Public REST interface exposing `GET /upload-url` with CORS and throttling. |

---

## 7.2 IAM Least-Privilege Matrix

| Role | Actions Permitted | Scoped Resource ARN |
|---|---|---|
| **PresignedUrlGeneratorRole** | `s3:PutObject` | `arn:aws:s3:::<raw-bucket-name>/*` |
| **SQSConsumerRole** | `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes` | `arn:aws:sqs:<region>:<account>:<queue-name>` |
| **SQSConsumerRole** | `states:StartExecution` | `arn:aws:states:<region>:<account>:stateMachine:<workflow-name>` |
| **ImageProcessorRole** | `s3:GetObject` | `arn:aws:s3:::<raw-bucket-name>/*` |
| **ImageProcessorRole** | `s3:PutObject` | `arn:aws:s3:::<dest-bucket-name>/*` |
| **ImageProcessorRole** | `dynamodb:PutItem`, `dynamodb:UpdateItem` | `arn:aws:dynamodb:<region>:<account>:table/<table-name>` |
| **ImageProcessorRole** | `sns:Publish` | `arn:aws:sns:<region>:<account>:<topic-name>` |
| **CloudFront OAC** | `s3:GetObject` | `arn:aws:s3:::<dest-bucket-name>/*` (Condition: `AWS:SourceArn == <distribution-arn>`) |

---

## 7.3 CloudFormation Parameters

| Parameter | Type | Default Value | Description |
|---|---|---|---|
| `Environment` | `String` | `prod` | Deployment environment name (`dev`, `staging`, `prod`). |
| `NotificationEmail`| `String` | *(Required)* | Email address to receive pipeline completion alerts and DLQ alarms. |
| `ThumbnailWidth` | `Number` | `200` | Width in pixels for generated thumbnail images. |
| `WatermarkText` | `String` | `CONFIDENTIAL` | Text watermark rendered on preview images. |
| `MaxFileSizeMB` | `Number` | `15` | Maximum allowable upload file size in megabytes. |

---

## 7.4 Operational Runbooks

### Runbook 1: Investigating Messages in the Dead-Letter Queue (DLQ)
When CloudWatch fires the alarm `ImageProcessingDLQAlarm`:
1. Open the **Amazon SQS Console** and navigate to `image-processing-dlq`.
2. Click **Send and receive messages** -> **Poll for messages**.
3. Inspect the message body to extract the S3 bucket and object key.
4. Verify whether the image was corrupted, exceeded memory limits, or contained invalid headers:
   ```bash
   aws s3 cp s3://<raw-bucket>/<failed-key> ./debug-image.bin
   file ./debug-image.bin
   ```
5. If the failure was transient, click **Start DLQ redrive** in the SQS console to replay messages back to `image-processing-queue`.

### Runbook 2: Testing via AWS CLI
```bash
# 1. Request a Pre-signed Upload URL
RESPONSE=$(curl -s "https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/upload-url?filename=test.jpg&contentType=image/jpeg")
UPLOAD_URL=$(echo $RESPONSE | jq -r .uploadUrl)

# 2. Upload sample image directly to S3
curl -X PUT -T sample.jpg -H "Content-Type: image/jpeg" "$UPLOAD_URL"

# 3. Verify DynamoDB Metadata Entry
aws dynamodb scan --table-name ImageMetadata-prod
```
