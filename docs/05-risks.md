# 5. Risks & Mitigations

This document outlines the risk register, potential failure modes, threat vectors, and the corresponding architectural safeguards built into the Serverless Image Processing Pipeline.

---

## 5.1 Risk Register

| ID | Threat / Failure Mode | Likelihood | Impact | Severity | Mitigation Strategy |
|---|---|---|---|---|---|
| **R01** | **Recursive S3 Invocation Loop** | High (if unmitigated) | Critical | High | **Separate Buckets Pattern**: Raw source images and processed destination assets are stored in two entirely separate S3 buckets (`raw-images-bucket` and `processed-images-bucket`). S3 event notifications are strictly bound only to `raw-images-bucket` and ignore the destination bucket, completely preventing infinite recursive execution loops. |
| **R02** | **Poison Pill / Corrupted Files** | Medium | Medium | Medium | **SQS Redrive Policy with DLQ**: Corrupted, zero-byte, or malformed image files that fail parsing in Lambda are retried up to 3 times before being shunted to the Dead-Letter Queue. A CloudWatch Alarm alerts operators, and the main queue continues processing healthy traffic. |
| **R03** | **Decompression Bomb ("Zip Bomb" / Giant Image)** | Low | High | Medium | **Early Validation & Memory Caps**: The `ValidateImage` task checks file size before loading full raster buffers into RAM. File size is strictly enforced <= 15MB. Pillow's built-in `Image.MAX_IMAGE_PIXELS` setting prevents memory exhaustion from decompression attacks. |
| **R04** | **Presigned URL Abuse / Endpoint Flooding** | Medium | Medium | Medium | **API Gateway Throttling & Short TTL**: The `GET /upload-url` endpoint has token-bucket rate limiting (100 req/sec, burst 200). Presigned URLs expire strictly in 15 minutes and require explicit `Content-Type` matching. |
| **R05** | **SQS Visibility Timeout Mismatch** | Medium | Medium | Medium | **Timeout Alignment**: In serverless queue architectures, SQS `VisibilityTimeout` must be >= 6x the Lambda timeout. Here, Lambda timeout is set to 30s, and SQS Visibility Timeout is set to 300s (10x), guaranteeing the message is not prematurely re-delivered while still processing. |
| **R06** | **CloudFront Origin Bypass / Unauthorized Access** | Low | High | Medium | **Origin Access Control (OAC)**: S3 Destination bucket policy explicitly blocks all public access and only accepts requests cryptographically signed by the CloudFront service principal matching the specific CloudFront distribution ARN. |
| **R07** | **Transient Downstream API Failures (DynamoDB / SNS)** | Medium | Low | Low | **Step Functions Exponential Retries**: The ASL definition configures automatic retry blocks with exponential backoff (`IntervalSeconds = 2`, `BackoffRate = 2.0`, `MaxAttempts = 3`) for `DynamoDb.ProvisionedThroughputExceededException` and `ServiceUnavailable`. |

---

## 5.2 Deep-Dive: Prevention of Recursive S3 Loops (The Anti-Pattern)

### The Danger:
In naive serverless image architectures, an engineer creates a single S3 bucket and configures an `s3:ObjectCreated:*` trigger to invoke Lambda. The Lambda resizes the image and writes `thumb-photo.jpg` back into the *same* bucket. This triggers another `s3:ObjectCreated` event, invoking Lambda again, creating an infinite recursive storm that exhausts AWS Lambda concurrency and can generate thousands of dollars in S3 and Lambda charges within hours.

### The Architectural Guardrail:
1. **Physical Isolation**: We deploy two physically distinct S3 buckets:
   - `SourceBucket`: Only receives raw uploads. S3 Event Notifications are enabled here.
   - `DestinationBucket`: Only receives processed assets (thumbnails, watermarked images). **No S3 event notifications exist on this bucket.**
2. **Distinct IAM Permissions**: The `PresignedUrlGenerator` only has `s3:PutObject` on the `SourceBucket`. The `ImageProcessor` only has `s3:GetObject` on `SourceBucket` and `s3:PutObject` on `DestinationBucket`.
