#!/bin/bash
# Build all Docker images and push them to AWS ECR.
# Prerequisites: aws CLI configured, Docker running, eksctl cluster already created.
#
# Usage: ./aws/ecr-push.sh <AWS_ACCOUNT_ID> [AWS_REGION]
#   e.g. ./aws/ecr-push.sh 123456789012 us-west-2

set -euo pipefail

AWS_ACCOUNT_ID=${1:?"Usage: $0 <AWS_ACCOUNT_ID> [AWS_REGION]"}
AWS_REGION=${2:-us-west-2}
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

SERVICES=(
  "user-service:backend/user-service"
  "restaurant-service:backend/restaurant-service"
  "owner-service:backend/owner-service"
  "review-service:backend/review-service"
  "review-worker:backend/review-worker"
  "restaurant-worker:backend/restaurant-worker"
  "user-worker:backend/user-worker"
  "frontend:frontend"
)

echo "==> Logging in to ECR at $ECR_REGISTRY"
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY"

for entry in "${SERVICES[@]}"; do
  NAME="${entry%%:*}"
  CONTEXT="${entry##*:}"
  REPO="${ECR_REGISTRY}/yelp/${NAME}"

  echo ""
  echo "==> Creating ECR repository yelp/${NAME} (skips if exists)"
  aws ecr describe-repositories --repository-names "yelp/${NAME}" \
    --region "$AWS_REGION" > /dev/null 2>&1 \
    || aws ecr create-repository --repository-name "yelp/${NAME}" \
        --region "$AWS_REGION" \
        --image-scanning-configuration scanOnPush=true \
        --tags Key=project,Value=yelp-clone

  echo "==> Building yelp/${NAME}"
  docker build \
    -f "${CONTEXT}/Dockerfile" \
    -t "${REPO}:latest" \
    .

  echo "==> Pushing yelp/${NAME}"
  docker push "${REPO}:latest"
done

echo ""
echo "All images pushed to ECR under ${ECR_REGISTRY}/yelp/"
echo "ECR_REGISTRY=${ECR_REGISTRY}"
