#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
BUCKET="msp-guardian-poc"
DDB_TABLE="msp_guardian_mappings"
DDB_CONNECTOR_REGISTRY="connector_registry"
GLUE_DB="msp_guardian_poc"
LAMBDA_NAME="testDatasourceConnection"
LAMBDA_SRC="/var/lambdas/test_datasource_connection"
SECRET_NAME="msp-guardian/placeholder"

echo "[bootstrap] creating S3 bucket: ${BUCKET}"
awslocal s3 mb "s3://${BUCKET}" --region "${REGION}" || true

echo "[bootstrap] creating S3 prefix markers"
for prefix in tmp samples landing raw curated quarantine reports mappings; do
  echo "" | awslocal s3 cp - "s3://${BUCKET}/${prefix}/.keep" || true
done

echo "[bootstrap] creating DynamoDB table: ${DDB_TABLE}"
awslocal dynamodb create-table \
  --table-name "${DDB_TABLE}" \
  --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=sk,AttributeType=S \
  --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region "${REGION}" || true

echo "[bootstrap] creating DynamoDB table: ${DDB_CONNECTOR_REGISTRY}"
awslocal dynamodb create-table \
  --table-name "${DDB_CONNECTOR_REGISTRY}" \
  --attribute-definitions AttributeName=source_id,AttributeType=S \
  --key-schema AttributeName=source_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region "${REGION}" || true

echo "[bootstrap] creating Glue database: ${GLUE_DB}"
awslocal glue create-database --database-input "Name=${GLUE_DB}" --region "${REGION}" || true

echo "[bootstrap] packaging + deploying Lambda: ${LAMBDA_NAME}"
ZIP_PATH="/tmp/${LAMBDA_NAME}.zip"
rm -f "${ZIP_PATH}"
(cd "${LAMBDA_SRC}" && zip -q "${ZIP_PATH}" handler.py)

if awslocal lambda get-function --function-name "${LAMBDA_NAME}" --region "${REGION}" >/dev/null 2>&1; then
  awslocal lambda update-function-code \
    --function-name "${LAMBDA_NAME}" \
    --zip-file "fileb://${ZIP_PATH}" \
    --region "${REGION}" || true
else
  awslocal lambda create-function \
    --function-name "${LAMBDA_NAME}" \
    --runtime python3.12 \
    --role arn:aws:iam::000000000000:role/lambda-role \
    --handler handler.handler \
    --zip-file "fileb://${ZIP_PATH}" \
    --region "${REGION}" || true
fi

echo "[bootstrap] creating placeholder Secrets Manager secret: ${SECRET_NAME}"
awslocal secretsmanager create-secret \
  --name "${SECRET_NAME}" \
  --secret-string '{"placeholder":true}' \
  --region "${REGION}" || true

echo "[bootstrap] done"
