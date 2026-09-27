# 3. Design Decisions & Tradeoffs

This document details the critical architectural choices made during the design of the Serverless Image Processing Pipeline, including the rationale, evaluated alternatives, and tradeoffs.

---

## 3.1 Architectural Decision Records (ADR)

| Decision | Selected Option | Alternatives Considered | Rationale & Tradeoffs |
|---|---|---|---|
| **ADR-01: Direct Upload Mechanism** | **S3 Pre-signed URLs via API Gateway** | 1. API Gateway HTTP POST with Binary Media Type.<br>2. Uploading through EC2 / ECS web container.<br>3. Direct public S3 bucket PUT. | **Rationale**: Routing large binary files through API Gateway introduces a 10 MB payload ceiling, increased latency, and API Gateway data transfer costs ($0.09/GB). Pre-signed URLs delegate the upload directly to S3's optimized multi-part network, keeping compute idle while providing cryptographic validation (SigV4).<br>**Tradeoff**: Requires a two-step client handshake (request pre-signed URL first, then PUT binary payload). |
| **ADR-02: Decoupling Layer** | **Amazon SQS with Dead-Letter Queue (DLQ)** | 1. Direct S3 Event Notification to AWS Lambda.<br>2. Amazon EventBridge Rule.<br>3. Amazon Kinesis Data Streams. | **Rationale**: Direct S3-to-Lambda invocation is an asynchronous push. If thousands of images are uploaded in seconds, Lambda may exceed account concurrency limits, leading to throttles and potential event loss after retry timeouts. SQS acts as a shock absorber (buffering traffic) and enables controlled concurrency (`batchSize = 5`, `maxConcurrency = 10`).<br>**Tradeoff**: Introduces a minor polling latency (usually < 200ms) compared to instantaneous direct invocation. |
| **ADR-03: Workflow Execution** | **AWS Step Functions (Standard Workflow)** | 1. Single monolithic Lambda doing all tasks.<br>2. Multiple Lambdas chaining via SNS/SQS.<br>3. Step Functions Express Workflow. | **Rationale**: A monolithic Lambda violates the Single Responsibility Principle, requires allocating maximum memory/timeout for the entire execution, and makes debugging intermediate failures difficult. Step Functions provides visual state inspection, per-task retry policies, and granular error catching (`Catch` block to DLQ).<br>**Tradeoff**: Additional state transition charges (offset by 4,000 free transitions/month under AWS Free Tier). |
| **ADR-04: Metadata Persistence Store** | **Amazon DynamoDB (On-Demand Capacity)** | 1. Amazon RDS PostgreSQL.<br>2. Amazon Aurora Serverless v2.<br>3. S3 Object Metadata / Tags. | **Rationale**: Image metadata is document-oriented (dimensions, EXIF, variant links) and requires single-digit millisecond latency at scale. DynamoDB On-Demand has zero idle base cost ($0.00 when idle), unlike RDS which requires provisioned DB instances or VPC NAT Gateways.<br>**Tradeoff**: DynamoDB has less complex relational query capabilities, but image catalog queries are simple key-value and GSI lookups (`user_id`). |
| **ADR-05: Global Edge Caching & Delivery** | **Amazon CloudFront with Origin Access Control (OAC)** | 1. Public S3 Bucket direct URLs.<br>2. CloudFront with Origin Access Identity (OAI).<br>3. CloudFront with S3 Website Endpoint. | **Rationale**: S3 buckets should never be public. CloudFront with OAC enforces SigV4 signed requests between CloudFront and S3, supports modern KMS encryption, enables HTTP/3 and TLS 1.3, caches images at 600+ edge locations worldwide, and eliminates repetitive S3 GET egress fees.<br>**Tradeoff**: Slight caching propagation delay when assets are updated (mitigated by immutable hashed filenames). |
| **ADR-06: Image Manipulation Engine** | **Python 3.12 with Pillow (PIL)** | 1. Node.js Sharp.<br>2. ImageMagick binary wrapper.<br>3. AWS Elemental MediaConvert. | **Rationale**: Pillow is the battle-tested standard for lightweight, efficient Python image resizing, thumbnailing, and alpha-composite watermarking. It runs seamlessly within standard AWS Lambda environments with zero external binary dependencies.<br>**Tradeoff**: High-resolution 8K RAW processing requires higher Lambda memory allocation (512MB–1024MB). |
| **ADR-07: Error Handling & DLQ Strategy** | **SQS Redrive with maxReceiveCount = 3 + CloudWatch Alarm** | 1. Infinite automatic retries.<br>2. Discarding failing events silently.<br>3. Writing errors to S3 error bucket. | **Rationale**: Corrupted or malicious files (e.g., zero-byte files, zip bombs disguised as JPEGs) will consistently fail. Without a DLQ, Lambda would enter an infinite retry loop, wasting budget. After 3 attempts, the message moves to DLQ and fires a CloudWatch Alarm.<br>**Tradeoff**: Operators must monitor the DLQ and manually inspect or purge poison pills. |

---

## 3.2 Evaluation Matrix

| Metric | Monolithic EC2 App | Direct S3 -> Lambda | SQS + Step Functions (This Architecture) |
|---|---|---|---|
| **Idle Cost** | ~$35/mo (EC2 + NAT GW) | $0.00 (Serverless) | **$0.00 (Serverless)** |
| **Burst Resilience** | Poor (fixed instance size) | Moderate (risk of Lambda throttling) | **Excellent (SQS buffering)** |
| **Observability** | OS logs / SSH | CloudWatch Logs (scattered) | **Visual Step Functions execution graph** |
| **Blast Radius of Failures** | High (server crash) | Medium (batch fails) | **Low (single-item isolation to DLQ)** |
| **Global Latency** | High (central region) | High (central region) | **Sub-50ms via CloudFront Edge** |
| **Maintenance Burden** | High (OS patching, AMI updates) | Zero | **Zero** |
