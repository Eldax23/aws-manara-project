# 2. Architecture

![Architecture](../architecture/solution-architecture.png)

## 2.1 System Architecture Overview
The **Serverless Image Processing Pipeline** is architected as a distributed, decoupled, event-driven system. It eliminates single points of failure, automatically scales from zero to tens of thousands of concurrent requests, and maintains complete separation of concerns across ingestion, buffering, orchestration, transformation, and edge caching.

```
+----------------------------------------------------------------------------------------------------+
|                                    SOLUTION ARCHITECTURE WORKFLOW                                  |
+----------------------------------------------------------------------------------------------------+
                                      [ 1. GET /upload-url ]
 [ Web / Mobile Client ] ──────────────────────────────────────────> [ API Gateway ]
          │                                                               │
          │ [ 3. PUT s3://raw-images/image.jpg ]                          │ [ 2. Invoke ]
          │    (Direct Upload via Pre-signed URL)                         ▼
          ▼                                                   [ Presigned URL Lambda ]
 [ S3 Source Bucket ] ──[ 4. Event: s3:ObjectCreated ]──> [ Amazon SQS Queue ] ──> [ SQS DLQ ]
                                                                   │
                                                                   │ [ 5. Trigger Batch ]
                                                                   ▼
                                                       [ SQS Consumer Lambda ]
                                                                   │
                                                                   ▼
                                             +─────────────────────────────────────────+
                                             |     AWS STEP FUNCTIONS STATE MACHINE    |
                                             |                                         |
                                             |  [ Task 1: Validate Image (MIME/Size) ] |
                                             |                     │                   |
                                             |  [ Task 2: Extract Metadata & EXIF ]    |
                                             |                     │                   |
                                             |  [ Task 3: Generate WebP Thumbnails ]   |
                                             |                     │                   |
                                             |  [ Task 4: Apply Brand Watermark ]      |
                                             |                     │                   |
                                             |  [ Task 5: Save S3 & Catalog DynamoDB ] |
                                             |                     │                   |
                                             |  [ Task 6: Publish SNS Notification ]   |
                                             +─────────────────────┬───────────────────+
                                                                   │
                                       ┌───────────────────────────┼───────────────────────────┐
                                       ▼                           ▼                           ▼
                           [ S3 Destination Bucket ]     [ DynamoDB Metadata ]         [ Amazon SNS Topic ]
                                       │
                                       ▼ [ Origin Access Control (OAC) ]
                             [ Amazon CloudFront CDN ]
                                       │
                                       ▼
                             [ Global Edge Users ]
```

---

## 2.2 Core Architectural Components

### 1. Ingestion & Secure Upload Tier
- **Amazon API Gateway (REST API)**: Provides a public REST endpoint (`GET /upload-url`) configured with CORS headers, request parameter validation, and rate limiting (throttling to 100 requests/sec with burst to 200).
- **Presigned URL Lambda (`presigned-url-generator`)**: Generates an Amazon S3 pre-signed URL valid for 15 minutes. It binds `content-type`, max file size conditions, and unique UUID object keys.
- **Amazon S3 Source Bucket (`raw-images`)**:
  - Private bucket with `BlockPublicAccess` enabled on all 4 settings.
  - Server-Side Encryption with Amazon S3 managed keys (`SSE-S3` or `SSE-KMS`).
  - Strict bucket policy enforcing HTTPS in transit (`aws:SecureTransport: "true"`).
  - Lifecycle rule transitioning uncompressed raw uploads to S3 Glacier Flexible Retrieval after 90 days.

### 2. Asynchronous Queue & Decoupling Tier
- **Amazon SQS Standard Queue (`image-processing-queue`)**:
  - Receives `s3:ObjectCreated:*` event notifications from the source bucket.
  - Decouples file uploads from downstream Lambda and Step Functions workers, smoothing out traffic spikes.
  - Visibility Timeout set to **300 seconds** (matching maximum expected processing duration).
  - Message Retention Period set to **4 days**.
- **Amazon SQS Dead-Letter Queue (DLQ) (`image-processing-dlq`)**:
  - Redrive policy: `maxReceiveCount = 3`. If a message fails processing 3 consecutive times, it is safely routed to the DLQ.
  - Retention period of **14 days** allows operators to inspect poisoned payloads and replay messages.
  - CloudWatch Alarm monitors `ApproximateNumberOfMessagesVisible > 0`.

### 3. Workflow Orchestration Tier (AWS Step Functions)
- **State Machine (`ImageProcessingWorkflow`)**:
  - Implemented using Amazon States Language (ASL).
  - Provides visual debugging, deterministic error recovery, retries with exponential backoff, and execution history.
  - **State Sequence**:
    1. `ValidateImage`: Checks file extension, MIME header, and guarantees size is under 15 MB.
    2. `ExtractMetadata`: Inspects image width, height, aspect ratio, color profile, and computes MD5 hash.
    3. `ResizeThumbnail`: Generates two optimized WebP variants:
       - `thumbnail`: 200x200 pixels (aspect-ratio preserved).
       - `preview`: 600x600 pixels.
    4. `ApplyWatermark`: Superimposes a translucent branded SVG/PNG watermark onto the preview image.
    5. `PersistAndCatalog`: Atomically writes the processed outputs into the S3 Destination bucket and records full metadata in DynamoDB.
    6. `PublishCompletion`: Dispatches an event payload to the Amazon SNS topic.

### 4. Storage, Edge Delivery & Persistence Tier
- **Amazon S3 Destination Bucket (`processed-images`)**:
  - Stores thumbnail, preview, and watermarked image objects.
  - All public access blocked. Accessible **only** by CloudFront via Origin Access Control (OAC) and the Step Functions IAM execution role.
- **Amazon CloudFront Distribution**:
  - Global Content Delivery Network (CDN) fronting the S3 destination bucket.
  - Enforces HTTPS (Redirect HTTP to HTTPS), TLS 1.3, and HTTP/3 support.
  - Caching optimized with `Managed-CachingOptimized` cache policy (1-year TTL with gzip & brotli compression).
- **Amazon DynamoDB (`ImageMetadataTable`)**:
  - On-Demand capacity mode (zero idle cost, seamless scale-to-zero).
  - Point-in-time recovery enabled.
  - Schema:
    - Primary Key: `image_id` (String - UUID)
    - Global Secondary Index (GSI): `user_id` (Partition Key) + `upload_timestamp` (Sort Key) for querying user galleries.
- **Amazon SNS Topic (`image-processing-alerts`)**:
  - Publishes pipeline execution alerts (success and DLQ failure alerts) to email, SMS, or webhook consumers.

---

## 2.3 Step-by-Step Request & Event Flow

| Step | Initiator | Target | Protocol / Action | Description |
|---|---|---|---|---|
| **1** | Client App | API Gateway | `GET /upload-url?filename=pic.jpg&contentType=image/jpeg` | Client requests permission to upload an image. |
| **2** | API Gateway | URL Lambda | AWS Lambda Invoke | Lambda generates an S3 Pre-signed URL with 15-min TTL and returns JSON `{ uploadUrl: "https://...", key: "raw/abc-123.jpg" }`. |
| **3** | Client App | S3 Source Bucket | `PUT https://...` (Direct Upload) | Client directly streams the binary image file to S3. No compute server bandwidth consumed. |
| **4** | S3 Source | Amazon SQS | S3 Event Notification (`s3:ObjectCreated:*`) | S3 automatically generates an event message and pushes it into the SQS queue. |
| **5** | SQS | SQS Consumer Lambda | Event Source Mapping (Batch Size = 5) | Lambda polls the queue, parses bucket and key, and executes the Step Functions State Machine. |
| **6** | Step Functions | Task Lambdas | Step Functions ASL Execution | State Machine executes: Validate → Extract Metadata → Resize → Watermark. |
| **7** | Task Lambda | S3 Destination & DynamoDB | S3 `PutObject` & DynamoDB `PutItem` | Resized/watermarked images stored in destination bucket; structured technical metadata written to DynamoDB. |
| **8** | Task Lambda | Amazon SNS | SNS `Publish` | Event notification published to subscribers containing asset links and execution metrics. |
| **9** | Client / Web | CloudFront | `GET https://d111111abcdef8.cloudfront.net/thumbnails/abc-123_thumb.webp` | Users view the optimized image via global edge caches. |

---

## 2.4 DynamoDB Data Schema

### Table: `ImageMetadata`
- **Billing Mode**: `PAY_PER_REQUEST` (On-Demand)
- **Partition Key**: `image_id` (String, e.g., `img_9f4c3a21-7b89-4d6e-912c-0e8fa7654321`)

#### Sample Item:
```json
{
  "image_id": "img_9f4c3a21-7b89-4d6e-912c-0e8fa7654321",
  "user_id": "user_demo_42",
  "upload_timestamp": "2026-09-27T08:30:00Z",
  "original_filename": "landscape.jpg",
  "file_size_bytes": 4194304,
  "mime_type": "image/jpeg",
  "dimensions": {
    "width": 3840,
    "height": 2160,
    "aspect_ratio": "16:9"
  },
  "md5_checksum": "d41d8cd98f00b204e9800998ecf8427e",
  "processing_status": "COMPLETED",
  "pipeline_duration_ms": 782,
  "variants": {
    "thumbnail": {
      "key": "thumbnails/img_9f4c3a21_thumb.webp",
      "width": 200,
      "height": 113,
      "cdn_url": "https://d123456abcdef.cloudfront.net/thumbnails/img_9f4c3a21_thumb.webp"
    },
    "preview": {
      "key": "previews/img_9f4c3a21_preview.webp",
      "width": 600,
      "height": 338,
      "cdn_url": "https://d123456abcdef.cloudfront.net/previews/img_9f4c3a21_preview.webp"
    },
    "watermarked": {
      "key": "watermarked/img_9f4c3a21_wm.webp",
      "width": 600,
      "height": 338,
      "cdn_url": "https://d123456abcdef.cloudfront.net/watermarked/img_9f4c3a21_wm.webp"
    }
  }
}
```

#### Global Secondary Index: `UserIndex`
- **Partition Key**: `user_id` (String)
- **Sort Key**: `upload_timestamp` (String)
- **Projection**: `ALL`
- **Use Case**: Enables instantaneous query of all photos uploaded by a specific user sorted chronologically.

---

## 2.5 Security Boundaries & Network Isolation

```
 Internet (Clients)
         │
         ├─── HTTPS ───> CloudFront (Edge PoPs) ──[ OAC / SigV4 ]──> S3 Destination
         │
         ├─── HTTPS ───> API Gateway ──[ IAM Auth ]──> Presigned URL Lambda
         │
         └─── HTTPS PUT ──[ SigV4 Presigned URL ]───> S3 Source
                                                          │
                                               [ S3 Event Notification ]
                                                          ▼
                                                  AWS Managed Fabric
                                            (SQS -> Lambda -> Step Functions)
```

1. **Origin Access Control (OAC)**: S3 Destination bucket completely blocks direct internet traffic. The bucket policy specifies `Principal: Service: cloudfront.amazonaws.com` with a condition matching the CloudFront Distribution ARN (`AWS:SourceArn`).
2. **Short-Lived Signed URLs**: Upload credentials expire in 15 minutes, limiting potential misuse if a URL is intercepted.
3. **IAM Least Privilege**: Each function execution role is granted permissions only to its exact bucket ARNs, SQS queue ARN, and DynamoDB table ARN.
