#!/usr/bin/env bash
set -euxo pipefail

REGION=ap-northeast-2
ACCOUNT=373317459179
REPO=app/backend
IMG=${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/${REPO}
TAG=${1:-latest}

# ECR 로그인
aws ecr get-login-password --region $REGION \
| docker login --username AWS --password-stdin ${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com

# compose 재배포
cd /opt/backend
BACK_IMAGE="${IMG}:${TAG}" docker compose up -d --pull always --force-recreate

docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
curl -fsS http://127.0.0.1:8000/v1/health >/dev/null