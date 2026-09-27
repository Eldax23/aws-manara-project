# 6. Future Work & Roadmap (v2)

While the current architecture provides a robust, production-grade serverless pipeline, the following enhancements are planned for version 2.0:

---

## 6.1 Planned Improvements

### 1. Automated Content Moderation with Amazon Rekognition
- **Objective**: Automatically flag inappropriate, explicit, or copyright-infringing content before it is published to the destination bucket.
- **Implementation**: Insert an `AnalyzeContent` task into the Step Functions state machine before the resize step. If `DetectModerationLabels` returns high-confidence unsafe categories, the workflow branches to quarantine the image in a private quarantine prefix and alerts compliance teams via SNS.

### 2. Multimodal AI Captioning & Tagging via Amazon Bedrock
- **Objective**: Generate semantic descriptions, alt-text, and searchable keywords for every uploaded image to optimize accessibility and search indexing.
- **Implementation**: Call Amazon Bedrock (Anthropic Claude 3 Haiku or Amazon Titan Multimodal) with the image buffer to output automated alt-text, saved directly into the DynamoDB item.

### 3. Migration to Amazon EventBridge Pipes
- **Objective**: Eliminate custom polling code in the SQS consumer Lambda.
- **Implementation**: Connect Amazon SQS directly to the AWS Step Functions State Machine using **EventBridge Pipes** with built-in input filtering and payload transformations, further reducing Lambda invocations and lines of code.

### 4. Smart Cropping & Focal Point Detection
- **Objective**: Avoid awkward image cropping when generating square avatars or banner thumbnails.
- **Implementation**: Use Rekognition `DetectFaces` to locate coordinates of the primary subject or face and crop around the focal point rather than a naive center-crop.

### 5. Multi-Region Active-Active DR with S3 Cross-Region Replication (CRR)
- **Objective**: Ensure business continuity against rare AWS regional outages.
- **Implementation**: Configure S3 Cross-Region Replication from the primary destination bucket (e.g., `us-east-1`) to a secondary region (e.g., `eu-west-1`), combined with Amazon DynamoDB Global Tables and Route 53 Latency-Based / Failover DNS.
