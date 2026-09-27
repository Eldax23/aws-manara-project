# 4. Well-Architected Framework Alignment

This project adheres to the best practices defined in the **AWS Well-Architected Framework** across all six pillars.

---

## 4.1 Pillar 1: Operational Excellence

| Best Practice | Implementation in this Architecture |
|---|---|
| **Infrastructure as Code (IaC)** | 100% of resources (S3, SQS, DynamoDB, Lambda, Step Functions, CloudFront, Alarms) are defined in modular AWS CloudFormation templates (`cloudformation/`). |
| **Comprehensive Observability** | CloudWatch Logs captures structured JSON logs across all Lambda functions with request IDs for distributed tracing. |
| **Visual Workflow Monitoring** | AWS Step Functions provides full execution history with step-by-step state inspection, execution timelines, and error stack traces. |
| **Automated Alerting** | CloudWatch Alarms continuously monitor the Dead-Letter Queue depth (`ApproximateNumberOfMessagesVisible > 0`) and Lambda error rates, alerting via Amazon SNS. |

---

## 4.2 Pillar 2: Security

| Best Practice | Implementation in this Architecture |
|---|---|
| **Zero Public Buckets** | Both S3 Source and Destination buckets have `BlockPublicAccess` enabled on all 4 settings (`BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`, `RestrictPublicBuckets`). |
| **Origin Access Control (OAC)** | The Destination S3 bucket is accessible only via CloudFront using SigV4 Origin Access Control. Direct HTTP access is completely blocked. |
| **Data Protection in Transit** | S3 bucket policies enforce TLS 1.2+ by rejecting non-SSL requests (`aws:SecureTransport: "false"`). CloudFront enforces HTTPS redirect. |
| **Data Protection at Rest** | S3 buckets use Server-Side Encryption (`SSE-S3` / `SSE-KMS`). DynamoDB uses AWS-managed encryption keys. |
| **Least-Privilege IAM Roles** | Each Lambda execution role and Step Functions role has explicit IAM statements scoped strictly to the exact ARN of the resources it touches. |
| **Short-Lived Credentials** | Direct uploads use time-delimited S3 Pre-signed URLs expiring in 15 minutes, preventing credential hoarding. |

---

## 4.3 Pillar 3: Reliability

| Best Practice | Implementation in this Architecture |
|---|---|
| **Decoupling with SQS** | Ingestion of image upload events is decoupled from image processing using an Amazon SQS Queue, preventing spike-induced timeouts. |
| **Fault Isolation with DLQ** | Poison messages and corrupted files are automatically moved to a Dead-Letter Queue after 3 failed attempts, preventing pipeline head-of-line blocking. |
| **Exponential Backoff Retries** | Step Functions state transitions and Lambda error handlers employ exponential backoff with jitter on transient failures. |
| **Multi-AZ by Design** | S3, SQS, DynamoDB, Lambda, and Step Functions are regional AWS serverless services that automatically replicate across at least 3 Availability Zones. |

---

## 4.4 Pillar 4: Performance Efficiency

| Best Practice | Implementation in this Architecture |
|---|---|
| **Direct Client-to-S3 Uploads** | Bypasses intermediate compute servers and API Gateway payload limits, maximizing client upload bandwidth. |
| **Global Edge Caching** | Amazon CloudFront caches processed thumbnails and preview images at 600+ edge locations worldwide, drastically reducing round-trip time. |
| **Single-Digit Millisecond NoSQL** | DynamoDB provides sub-10ms read/write response times for metadata queries and user gallery lookups. |
| **Optimized Image Formats** | Images are converted to modern WebP format, achieving a 30%–70% reduction in file size compared to original JPEGs/PNGs without visual quality loss. |

---

## 4.5 Pillar 5: Cost Optimization

| Best Practice | Implementation in this Architecture |
|---|---|
| **100% Serverless Pay-per-Use** | Zero idle infrastructure. When no images are being uploaded, monthly cost is **$0.00**. |
| **Full AWS Free Tier Compliance** | The entire architecture operates comfortably within Free Tier allowances (1M Lambda requests, 1M SQS messages, 25 GB DynamoDB, 1 TB CloudFront). |
| **S3 Lifecycle Tiering** | Raw image uploads transition to S3 Glacier Flexible Retrieval after 90 days, cutting raw storage costs by over 80%. |
| **Bandwidth Offload via CDN** | CloudFront serves repeat requests from edge cache, reducing billable S3 GET requests and data transfer out costs. |

---

## 4.6 Pillar 6: Sustainability

| Best Practice | Implementation in this Architecture |
|---|---|
| **Energy-Efficient Compute** | Serverless compute runs only when work is queued; zero idle electricity consumption. |
| **Compressed Asset Sizes** | Converting images to WebP reduces network transmission payloads, reducing energy spent across the global internet infrastructure. |
| **Resource Right-Sizing** | Lambda functions are allocated tailored memory configurations (256MB–512MB) matching workload demands without overprovisioning. |
