#!/bin/bash
# Full end-to-end deploy to AWS EKS.
#
# Usage: ./aws/deploy-to-eks.sh <AWS_ACCOUNT_ID> [AWS_REGION] [CLUSTER_NAME]
#   e.g. ./aws/deploy-to-eks.sh 123456789012 us-west-2 yelp-cluster
#
# What this does:
#   1. Creates the EKS cluster (if it doesn't exist)
#   2. Builds + pushes all Docker images to ECR
#   3. Installs AWS Load Balancer Controller via Helm
#   4. Applies all k8s manifests, patching image URLs to use ECR
#   5. Waits for rollout and prints the ALB endpoint

set -euo pipefail

AWS_ACCOUNT_ID=${1:?"Usage: $0 <AWS_ACCOUNT_ID> [AWS_REGION] [CLUSTER_NAME]"}
AWS_REGION=${2:-us-west-2}
CLUSTER_NAME=${3:-yelp-cluster}
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# ── 1. Create EKS cluster ────────────────────────────────────────────────────
echo "==> Checking if EKS cluster '${CLUSTER_NAME}' exists..."
if eksctl get cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" > /dev/null 2>&1; then
  echo "    Cluster already exists, skipping creation."
else
  echo "==> Creating EKS cluster (this takes ~15 minutes)..."
  eksctl create cluster -f aws/eks-cluster.yaml
fi

# ── 2. Update kubeconfig ─────────────────────────────────────────────────────
echo "==> Updating kubeconfig..."
aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME"

# ── 3. Build + push images to ECR ───────────────────────────────────────────
echo "==> Building and pushing images to ECR..."
./aws/ecr-push.sh "$AWS_ACCOUNT_ID" "$AWS_REGION"

# ── 4. Install AWS Load Balancer Controller ──────────────────────────────────
echo "==> Installing AWS Load Balancer Controller..."
# Create IAM service account for ALB controller
eksctl create iamserviceaccount \
  --cluster="$CLUSTER_NAME" \
  --region="$AWS_REGION" \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess \
  --override-existing-serviceaccounts \
  --approve 2>/dev/null || true

helm repo add eks https://aws.github.io/eks-charts 2>/dev/null || true
helm repo update
helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName="$CLUSTER_NAME" \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --wait

# ── 5. Apply k8s manifests with ECR image URLs ───────────────────────────────
echo "==> Applying Kubernetes manifests..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/aws-storageclass.yaml
kubectl apply -f k8s/mongodb.yaml
kubectl apply -f k8s/kafka.yaml

# Patch image fields with actual ECR URLs
SERVICES=(
  "user-service"
  "restaurant-service"
  "owner-service"
  "review-service"
)
WORKERS=(
  "review-worker"
  "restaurant-worker"
  "user-worker"
)

for svc in "${SERVICES[@]}"; do
  sed "s|yelp/${svc}:latest|${ECR_REGISTRY}/yelp/${svc}:latest|g" \
    "k8s/${svc}.yaml" | kubectl apply -f -
done

# Workers + frontend
sed "s|yelp/review-worker:latest|${ECR_REGISTRY}/yelp/review-worker:latest|g; \
     s|yelp/restaurant-worker:latest|${ECR_REGISTRY}/yelp/restaurant-worker:latest|g; \
     s|yelp/user-worker:latest|${ECR_REGISTRY}/yelp/user-worker:latest|g" \
  k8s/workers.yaml | kubectl apply -f -

sed "s|yelp/frontend:latest|${ECR_REGISTRY}/yelp/frontend:latest|g" \
  k8s/frontend.yaml | kubectl apply -f -

kubectl apply -f k8s/aws-ingress.yaml

# ── 6. Wait and print endpoint ───────────────────────────────────────────────
echo ""
echo "==> Waiting for deployments to roll out..."
for svc in user-service restaurant-service owner-service review-service frontend; do
  kubectl rollout status deployment/"$svc" -n yelp --timeout=300s
done

echo ""
echo "==> Waiting for ALB to provision (up to 3 minutes)..."
for i in $(seq 1 18); do
  ALB_HOST=$(kubectl get ingress yelp-alb-ingress -n yelp \
    -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)
  if [[ -n "$ALB_HOST" ]]; then
    break
  fi
  sleep 10
done

echo ""
echo "========================================="
echo "  Deployment complete!"
echo "  App URL:  http://${ALB_HOST:-<pending — check: kubectl get ingress -n yelp>}"
echo "  Swagger:"
echo "    User Service:       http://${ALB_HOST}/auth/docs  (via port-forward: localhost:8001/docs)"
echo "    Restaurant Service: http://${ALB_HOST}/restaurants/docs"
echo "    Owner Service:      http://${ALB_HOST}/owner/docs"
echo "    Review Service:     http://${ALB_HOST}/reviews/docs"
echo "========================================="
