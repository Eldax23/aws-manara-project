# 1. Requirements

## 1.1 Project Overview & Objective
This project implements a production-grade, event-driven **Serverless Image Processing Pipeline** on Amazon Web Services (AWS). It is designed to demonstrate key competencies required for the **AWS Certified Solutions Architect – Associate (SAA-C03)** certification and the **Manara AWS Graduation Project**.

The solution ingests user-uploaded media files securely, decouples upload bursts using message queues, orchestrates multi-step transformation tasks (validation, EXIF metadata extraction, thumbnail creation, and watermarking) through AWS Step Functions, catalogs processed metadata in Amazon DynamoDB, and distributes optimized assets worldwide via Amazon CloudFront with sub-millisecond edge latency.

---

## 1.2 Functional Requirements

| ID | Requirement | Description |
|---|---|---|
| **FR-01** | **Direct-to-S3 Uploads** | The architecture must allow web and mobile clients to upload raw image assets directly to Amazon S3 using time-delimited, cryptographically signed Pre-signed URLs without routing heavy media payloads through compute servers or API Gateway. |
| **FR-02** | **Asynchronous Decoupling** | Media uploads must trigger asynchronous processing via Amazon S3 Event Notifications published to an Amazon SQS Queue, protecting downstream compute resources from throughput spikes. |
| **FR-03** | **Poisoned Message Handling** | The message queue must be paired with a Dead-Letter Queue (DLQ) configured with a redrive policy (`maxReceiveCount = 3`) to isolate corrupted or malformed payloads without blocking the queue. |
| **FR-04** | **Multi-Step Orchestration** | Image transformations must execute through a managed state machine in AWS Step Functions adhering to the sequence: **Validate Image → Extract Metadata → Generate Thumbnails → Apply Watermark → Store & Catalog → Notify**. |
| **FR-05** | **Multi-Format Processing** | The processing engine must support standard image formats (JPEG, PNG, WebP) and generate multiple responsive resolutions (e.g., thumbnail `200x200` and preview `600x600`). |
| **FR-06** | **Metadata Persistence** | Extracted technical metadata (file size, dimensions, MIME type, MD5 checksum, color depth, aspect ratio, and timestamps) must be persisted in an Amazon DynamoDB table with low-latency querying. |
| **FR-07** | **Edge Content Delivery** | Processed assets in the destination S3 bucket must be cached globally and served over HTTPS using an Amazon CloudFront distribution protected with Origin Access Control (OAC). |
| **FR-08** | **Event Notification Fan-out** | Upon successful pipeline execution, an Amazon SNS Topic must publish an event payload to subscribed endpoints (e.g., email notifications, downstream application webhooks). |

---

## 1.3 Non-Functional Requirements

### 1.3.1 Performance & Scalability
- **Auto-Scaling Compute**: Compute tasks must run on AWS Lambda, automatically scaling horizontally with zero server provisioning or cold-instance idling.
- **Latency Optimization**: Global asset retrieval latency must be minimized by CloudFront edge points of presence (PoPs) using HTTP/3 and TLS 1.3.
- **Queue Buffering**: Amazon SQS must support virtually unlimited ingestion throughput with standard queue semantics.

### 1.3.2 Security & Least Privilege
- **Zero Server Management**: Elimination of EC2 instances, SSH key pairs, bastion hosts, and open ingress ports.
- **Strict IAM Policies**: Every Lambda execution role and Step Functions execution role must adhere to least-privilege principles with scoped resource ARNs.
- **Data Protection at Rest & in Transit**:
  - All S3 buckets must enforce Server-Side Encryption (`AES256` / `aws:kms`), Block Public Access enabled across all 4 settings, and TLS 1.2+ in bucket policies (`aws:SecureTransport: "true"`).
  - S3 Destination Bucket must restrict direct public access and only accept signed CloudFront Origin Access Control (OAC) requests.
- **DynamoDB Security**: Encryption at rest enabled using AWS owned/managed keys, with Point-in-Time Recovery (PITR) support.

### 1.3.3 Reliability & Fault Tolerance
- **Automatic Retries & Backoff**: AWS Step Functions state transitions and Lambda error handlers must utilize exponential backoff retries for transient S3 or DynamoDB exceptions.
- **DLQ Redrive**: Messages failing processing 3 times are retained in the DLQ for 14 days, triggering CloudWatch alerts for operational remediation.
- **Multi-AZ Resilience**: All serverless services (S3, SQS, Lambda, Step Functions, DynamoDB) inherently operate across multiple Availability Zones with high availability.

### 1.3.4 Cost Efficiency (100% Free Tier Viable)
- All utilized AWS services fit entirely within the **AWS Free Tier**:
  - **AWS Lambda**: 1,000,000 free requests/month and 3.2 million seconds of compute time.
  - **Amazon S3**: 5 GB of standard storage, 20,000 GET requests, and 2,000 PUT requests.
  - **Amazon SQS**: 1,000,000 free requests/month.
  - **Amazon DynamoDB**: 25 GB of storage and 25 write/read capacity units (on-demand mode).
  - **Amazon CloudFront**: 1 TB of data transfer out per month.
  - **AWS Step Functions**: 4,000 free state transitions per month.
  - **Amazon SNS**: 1,000,000 mobile push notifications / 100,000 HTTP/S notifications / 1,000 email alerts.
- Zero idle running cost ($0.00/hour when no images are being processed).

---

## 1.4 SAA-C03 Exam Domain Alignment

| SAA-C03 Domain | Weight | Architectural Alignment in this Project |
|---|---|---|
| **Domain 1: Design Secure Architectures** | 30% | Direct S3 uploads via Pre-signed URLs, CloudFront Origin Access Control (OAC), least-privilege IAM execution roles, S3 bucket encryption, TLS enforcement (`aws:SecureTransport`). |
| **Domain 2: Design Resilient Architectures** | 26% | SQS decoupling for burst absorption, Dead-Letter Queues (DLQ) for poison messages, Step Functions error catching (`Catch` / `Retry`), multi-AZ serverless execution. |
| **Domain 3: Design High-Performing Architectures** | 24% | Event-driven triggers, CloudFront edge caching, DynamoDB single-digit millisecond reads/writes, asynchronous multi-stage execution. |
| **Domain 4: Design Cost-Optimized Architectures** | 20% | 100% serverless pay-per-use model ($0 idle cost), S3 Lifecycle policies (transition to Glacier / expiration), optimal Lambda memory sizing. |

---

## 1.5 Scope & Boundaries

### In Scope
1. CloudFormation templates for automated provisioning of all AWS infrastructure.
2. Production-ready Python Lambda source code for URL generation, SQS consumption, and image manipulation.
3. AWS Step Functions state machine workflow definition in Amazon States Language (ASL).
4. CloudWatch alarms for DLQ message backlog and execution errors.
5. Interactive browser-based test client and automated integration testing scripts.

### Out of Scope
- User authentication and sign-up flows (e.g., Amazon Cognito) — pre-signed URLs are issued via authenticated or API-key throttled endpoints.
- Heavy video transcoding (e.g., AWS Elemental MediaConvert) — focused strictly on images and visual media assets.
