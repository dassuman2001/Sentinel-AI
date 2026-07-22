#!/bin/bash
set -e

# Configuration
S3_BUCKET="$1"
CLOUDFRONT_DIST_ID="$2"
API_URL="$3"

if [ -z "$S3_BUCKET" ] || [ -z "$CLOUDFRONT_DIST_ID" ] || [ -z "$API_URL" ]; then
  echo "Usage: ./deploy.sh <S3_BUCKET_NAME> <CLOUDFRONT_DISTRIBUTION_ID> <API_ALB_URL>"
  exit 1
fi

echo "=== 1. Building Frontend React Application ==="
cd frontend
npm install
VITE_API_URL="$API_URL" npm run build
cd ..

echo "=== 2. Uploading static assets to Amazon S3 ==="
aws s3 sync frontend/dist/ s3://${S3_BUCKET} --delete

echo "=== 3. Invalidating CloudFront Cache for Instant Updates ==="
aws cloudfront create-invalidation --distribution-id ${CLOUDFRONT_DIST_ID} --paths "/*"

echo "=== Deployment Completed Successfully! ==="
