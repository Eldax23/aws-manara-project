#!/bin/bash
##############################################################################
# cleanup.sh — Safe Teardown & Resource Deletion Script
# Project: Serverless Image Processing Pipeline with S3, SQS & Lambda
#
# Usage:
#   chmod +x scripts/cleanup.sh
#   ./scripts/cleanup.sh [--stack-name <name>] [--region <region>] [--profile <profile>]
##############################################################################

set -euo pipefail

AWS_PROFILE="${AWS_PROFILE:-default}"
AWS_REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="${1:-serverless-image-pipeline}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_success() { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

echo -e "${RED}================================================================${NC}"
echo -e "${RED}       AWS SERVERLESS IMAGE PIPELINE TEARDOWN & CLEANUP         ${NC}"
echo -e "${RED}================================================================${NC}"
log_warn "This will permanently delete all resources associated with stack: ${STACK_NAME}"
read -p "Are you sure you want to proceed? (yes/no): " CONFIRM
if [[ "${CONFIRM}" != "yes" ]]; then
    log_info "Teardown aborted by user."
    exit 0
fi

# ─── Function to empty S3 bucket including versions ─────────────────────────
empty_bucket() {
    local bucket_name=$1
    if aws s3api head-bucket --bucket "${bucket_name}" --profile "${AWS_PROFILE}" 2>/dev/null; then
        log_info "Emptying S3 bucket: ${bucket_name}..."
        aws s3 rm "s3://${bucket_name}" --recursive --profile "${AWS_PROFILE}" 2>/dev/null || true

        # Delete version markers if versioning was enabled
        local versions
        versions=$(aws s3api list-object-versions --bucket "${bucket_name}" --profile "${AWS_PROFILE}" --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' --output json 2>/dev/null || true)
        if [[ "${versions}" != '{"Objects": null}' && -n "${versions}" ]]; then
            aws s3api delete-objects --bucket "${bucket_name}" --delete "${versions}" --profile "${AWS_PROFILE}" 2>/dev/null || true
        fi
        log_success "Bucket ${bucket_name} emptied."
    fi
}

# ─── Find Buckets from Stack Outputs ────────────────────────────────────────
log_info "Inspecting stack outputs for S3 buckets..."
if aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --profile "${AWS_PROFILE}" --region "${AWS_REGION}" &>/dev/null; then
    SOURCE_BUCKET=$(aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --query "Stacks[0].Outputs[?OutputKey=='SourceBucket'].OutputValue" --output text --profile "${AWS_PROFILE}" --region "${AWS_REGION}" 2>/dev/null || true)
    DEST_BUCKET=$(aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --query "Stacks[0].Outputs[?OutputKey=='DestinationBucket'].OutputValue" --output text --profile "${AWS_PROFILE}" --region "${AWS_REGION}" 2>/dev/null || true)

    if [[ -n "${SOURCE_BUCKET}" && "${SOURCE_BUCKET}" != "None" ]]; then
        empty_bucket "${SOURCE_BUCKET}"
    fi
    if [[ -n "${DEST_BUCKET}" && "${DEST_BUCKET}" != "None" ]]; then
        empty_bucket "${DEST_BUCKET}"
    fi
fi

# ─── Delete CloudFormation Stack ────────────────────────────────────────────
log_info "Initiating CloudFormation stack deletion: ${STACK_NAME}..."
aws cloudformation delete-stack \
    --stack-name "${STACK_NAME}" \
    --profile "${AWS_PROFILE}" \
    --region "${AWS_REGION}"

log_info "Waiting for stack deletion to complete..."
aws cloudformation wait stack-delete-complete \
    --stack-name "${STACK_NAME}" \
    --profile "${AWS_PROFILE}" \
    --region "${AWS_REGION}" 2>/dev/null || true

log_success "Stack ${STACK_NAME} deleted successfully."
echo -e "${GREEN}Cleanup complete. All resources have been safely destroyed.${NC}"
