import boto3

from app.core.config import settings


def localstack_client(service: str):
    return boto3.client(
        service,
        endpoint_url=settings.AWS_ENDPOINT_URL,
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def real_aws_client(service: str):
    return boto3.client(service, region_name=settings.AWS_REPORT_REGION)
