#!/bin/bash
##############################################################################
# deploy.sh — Automated Deployment Script
# Project: Serverless Image Processing Pipeline with S3, SQS & Lambda
#
# Usage:
#   chmod +x scripts/deploy.sh
#   ./scripts/deploy.sh --email <admin-email> [--bucket <template-bucket>] [--region <aws-region>] [--profile <aws-profile>]
##############################################################################

set -euo pipefail

# ─── Defaults ───────────────────────────────────────────────────────────────
AWS_PROFILE="${AWS_PROFILE:-default}"
AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="prod"
PROJECT_NAME="ServerlessImagePipeline"
NOTIFICATION_EMAIL=""
TEMPLATE_BUCKET=""
STACK_NAME="serverless-image-pipeline"
DEPLOY_MODE="standalone" # "standalone" or "nested"

# ─── Color Codes ────────────────────────────────────────────────────────────
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

usage() {
    echo -e "${CYAN}Serverless Image Processing Pipeline Deployment${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --email <email>       Email for operational notifications & alarms (required)"
    echo "  --bucket <bucket>     S3 bucket for nested CloudFormation templates (required for --mode nested)"
    echo "  --mode <mode>         Deployment mode: 'standalone' (default, single template) or 'nested'"
    echo "  --region <region>     AWS Region (default: us-east-1)"
    echo "  --profile <profile>   AWS CLI Profile (default: default)"
    echo "  --env <environment>   Environment stage: dev, staging, prod (default: prod)"
    echo "  -h, --help            Show this help message"
    echo ""
    exit 1
}

# ─── Parse Arguments ────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --email)
            NOTIFICATION_EMAIL="$2"
            shift 2
            ;;
        --bucket)
            TEMPLATE_BUCKET="$2"
            shift 2
            ;;
        --mode)
            DEPLOY_MODE="$2"
            shift 2
            ;;
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown argument: $1"
            usage
            ;;
    esac
done

if [[ -z "${NOTIFICATION_EMAIL}" ]]; then
    log_error "Missing required argument: --email <admin-email>"
    usage
fi

if [[ "${DEPLOY_MODE}" == "nested" && -z "${TEMPLATE_BUCKET}" ]]; then
    log_error "Nested deployment mode requires: --bucket <template-bucket>"
    usage
fi

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}       AWS SERVERLESS IMAGE PROCESSING PIPELINE DEPLOYMENT       ${NC}"
echo -e "${CYAN}================================================================${NC}"
log_info "Region:        ${AWS_REGION}"
log_info "Profile:       ${AWS_PROFILE}"
log_info "Environment:   ${ENVIRONMENT}"
log_info "Alert Email:   ${NOTIFICATION_EMAIL}"
log_info "Deploy Mode:   ${DEPLOY_MODE}"

# ─── Validate AWS CLI ───────────────────────────────────────────────────────
if ! command -v aws &>/dev/null; then
    log_error "AWS CLI v2 is not installed or not in PATH."
    exit 1
fi

log_info "Checking AWS caller identity..."
CALLER_IDENTITY=$(aws sts get-caller-identity --profile "${AWS_PROFILE}" 2>&1) || {
    log_error "AWS credentials not valid or expired. Please run 'aws configure' or check credentials."
    echo "${CALLER_IDENTITY}"
    exit 1
}
ACCOUNT_ID=$(echo "${CALLER_IDENTITY}" | grep -o '"Account": "[^"]*' | cut -d'"' -f4)
log_success "Authenticated as Account: ${ACCOUNT_ID}"

# ─── Deployment Logic ───────────────────────────────────────────────────────
if [[ "${DEPLOY_MODE}" == "standalone" ]]; then
    TEMPLATE_PATH="cloudformation/standalone-deployment.yaml"
    log_info "Deploying standalone unified stack: ${STACK_NAME}"
    log_info "Template: ${TEMPLATE_PATH}"

    aws cloudformation deploy \
        --template-file "${TEMPLATE_PATH}" \
        --stack-name "${STACK_NAME}" \
        --parameter-overrides \
            Environment="${ENVIRONMENT}" \
            NotificationEmail="${NOTIFICATION_EMAIL}" \
        --capabilities CAPABILITY_NAMED_IAM \
        --tags Project="${PROJECT_NAME}" Environment="${ENVIRONMENT}" ManagedBy=CloudFormation \
        --profile "${AWS_PROFILE}" \
        --region "${AWS_REGION}"

else
    log_info "Syncing nested CloudFormation templates to s3://${TEMPLATE_BUCKET}/cloudformation/ ..."
    aws s3 sync cloudformation/ "s3://${TEMPLATE_BUCKET}/cloudformation/" \
        --exclude "standalone-deployment.yaml" \
        --profile "${AWS_PROFILE}" \
        --region "${AWS_REGION}"

    log_info "Deploying master nested stack: ${STACK_NAME}"
    aws cloudformation deploy \
        --template-file cloudformation/main-stack.yaml \
        --stack-name "${STACK_NAME}" \
        --parameter-overrides \
            Environment="${ENVIRONMENT}" \
            NotificationEmail="${NOTIFICATION_EMAIL}" \
            TemplateBucket="${TEMPLATE_BUCKET}" \
        --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
        --tags Project="${PROJECT_NAME}" Environment="${ENVIRONMENT}" ManagedBy=CloudFormation \
        --profile "${AWS_PROFILE}" \
        --region "${AWS_REGION}"
fi

log_success "Deployment completed successfully!"

echo ""
echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}                     STACK OUTPUTS & ENDPOINTS                  ${NC}"
echo -e "${CYAN}================================================================${NC}"
aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --query "Stacks[0].Outputs" \
    --output table \
    --profile "${AWS_PROFILE}" \
    --region "${AWS_REGION}"

echo ""
log_success "Next steps:"
echo "  1. Check your email (${NOTIFICATION_EMAIL}) and confirm the Amazon SNS subscription."
echo "  2. Run './scripts/test.sh' to execute integration verification."
echo "  3. Open 'client/index.html' in your browser to interact with the live upload interface."
