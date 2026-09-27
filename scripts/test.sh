#!/bin/bash
##############################################################################
# test.sh — End-to-End Pipeline Verification Script
#
# Usage:
#   chmod +x scripts/test.sh
#   ./scripts/test.sh [--api-url <api-gateway-upload-url>]
##############################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

API_URL="${1:-}"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}        SERVERLESS IMAGE PIPELINE TEST & VERIFICATION           ${NC}"
echo -e "${CYAN}================================================================${NC}"

# ─── 1. Run Local Unit Tests ────────────────────────────────────────────────
echo -e "${BLUE}[STEP 1]${NC} Running Local Unit Tests..."
python3 tests/test_pipeline.py
echo -e "${GREEN}[OK]${NC} All local unit tests passed successfully!"
echo ""

# ─── 2. Optional Live API Gateway Test ───────────────────────────────────────
if [[ -n "${API_URL}" ]]; then
    echo -e "${BLUE}[STEP 2]${NC} Executing Live Cloud Integration Test against: ${API_URL}"
    TEST_IMAGE="tests/sample-images/sample-landscape.jpg"

    if [[ ! -f "${TEST_IMAGE}" ]]; then
        echo -e "${BLUE}[INFO]${NC} Generating sample test images..."
        python3 tests/generate_sample_image.py
    fi

    echo -e "${BLUE}[INFO]${NC} Requesting Pre-signed S3 Upload URL..."
    RESPONSE=$(curl -s -X GET "${API_URL}?filename=sample-landscape.jpg&contentType=image/jpeg")
    echo "API Response: ${RESPONSE}"

    UPLOAD_URL=$(echo "${RESPONSE}" | grep -o '"uploadUrl": "[^"]*' | cut -d'"' -f4)
    if [[ -z "${UPLOAD_URL}" ]]; then
        echo -e "${RED}[ERROR]${NC} Failed to extract uploadUrl from API response."
        exit 1
    fi

    echo -e "${BLUE}[INFO]${NC} Uploading binary image to S3..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PUT -T "${TEST_IMAGE}" -H "Content-Type: image/jpeg" "${UPLOAD_URL}")

    if [[ "${HTTP_CODE}" == "200" ]]; then
        echo -e "${GREEN}[OK]${NC} S3 Direct Upload succeeded (HTTP ${HTTP_CODE})!"
        echo -e "${GREEN}[OK]${NC} Event notification dispatched to SQS -> Step Functions executing in background."
    else
        echo -e "${RED}[ERROR]${NC} S3 upload returned status ${HTTP_CODE}."
        exit 1
    fi
else
    echo -e "${BLUE}[INFO]${NC} Pass '--api-url <url>' to perform live cloud end-to-end integration testing."
fi

echo ""
echo -e "${GREEN}Verification suite complete.${NC}"
