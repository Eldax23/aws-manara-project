# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-27

### Added
- **Solution Architecture Diagrams**:
  - High-resolution architecture visual diagram (`architecture/solution-architecture.png`).
  - Scalable vector diagram (`architecture/solution-architecture.svg`).
  - Editable draw.io / diagrams.net XML specification (`architecture/solution-architecture.drawio`).
- **Complete Documentation Suite**:
  - `docs/01-requirements.md`: Functional and non-functional requirements aligned with SAA-C03 domains.
  - `docs/02-architecture.md`: In-depth component breakdowns, numbered request flows, DynamoDB schema, and OAC configuration.
  - `docs/03-design-decisions.md`: Architectural Decision Records (ADRs) with rationale and tradeoffs.
  - `docs/04-well-architected.md`: Complete mapping across all 6 AWS Well-Architected Framework pillars.
  - `docs/05-risks.md`: Threat vectors, risk register, and failure mode mitigations (e.g. recursive S3 prevention).
  - `docs/06-future-work.md`: Roadmap for v2 (Amazon Rekognition moderation and Bedrock multimodal AI).
  - `docs/07-appendix.md`: Complete AWS service inventory, CloudFormation parameters, and operational runbooks.
- **Infrastructure as Code (CloudFormation)**:
  - `cloudformation/01-storage-queues.yaml`: S3 buckets, SQS queue, and Dead-Letter Queue with redrive policy.
  - `cloudformation/02-database-notifications.yaml`: DynamoDB metadata table with GSI and SNS alerts topic.
  - `cloudformation/03-iam-roles.yaml`: Least-privilege IAM execution roles for Lambda and Step Functions.
  - `cloudformation/04-step-functions.yaml`: Step Functions state machine ASL implementation.
  - `cloudformation/05-lambda-functions.yaml`: Lambda functions and SQS event source mapping.
  - `cloudformation/06-api-gateway.yaml`: REST API with CORS and rate throttling.
  - `cloudformation/07-cloudfront.yaml`: CloudFront CDN distribution with Origin Access Control (OAC).
  - `cloudformation/08-monitoring.yaml`: CloudWatch DLQ depth alarm, Lambda error alarms, and operations dashboard.
  - `cloudformation/main-stack.yaml`: Master orchestrator for nested stack deployments.
  - `cloudformation/standalone-deployment.yaml`: All-in-one template for zero-dependency instant deployments.
- **Python Lambda Functions (`lambda/`)**:
  - `presigned-url-generator`: Cryptographic S3 PUT signer with content-type enforcement.
  - `sqs-consumer`: Event source processor launching Step Functions executions.
  - `image-processor`: High-quality WebP thumbnail generation, EXIF metadata extraction, and watermarking using Pillow.
  - `notification-dispatcher`: SNS alert formatter and publisher.
- **Interactive Web Demo & Test Client (`client/index.html`)**:
  - Clean HTML5/CSS/JS frontend to test direct uploads via pre-signed URLs and live previews.
- **Automated Verification Suite (`tests/` & `scripts/`)**:
  - `tests/test_pipeline.py`: Comprehensive unit tests.
  - `tests/generate_sample_image.py`: Test asset generator.
  - `scripts/deploy.sh`: Automated multi-mode deployment script.
  - `scripts/cleanup.sh`: Safe teardown and bucket emptying script.
  - `scripts/test.sh`: One-click test runner.
