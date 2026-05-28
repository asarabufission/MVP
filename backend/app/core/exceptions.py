from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    default_detail: str = "Internal server error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class InvalidCredentialsError(AppError):
    status_code = 401
    code = "INVALID_CREDENTIALS"
    default_detail = "Invalid username or password"


class TokenExpiredError(AppError):
    status_code = 401
    code = "TOKEN_EXPIRED"
    default_detail = "Access token is missing or expired"


class InvalidRefreshTokenError(AppError):
    status_code = 401
    code = "INVALID_REFRESH_TOKEN"
    default_detail = "Refresh token is invalid or expired"


class RoleForbiddenError(AppError):
    status_code = 403
    code = "ROLE_FORBIDDEN"
    default_detail = "Your role does not permit this action"


class MspMismatchError(AppError):
    status_code = 403
    code = "MSP_MISMATCH"
    default_detail = "Resource does not belong to your MSP"


class ClientNameTakenError(AppError):
    status_code = 409
    code = "CLIENT_NAME_TAKEN"
    default_detail = "A client with this name already exists"


class AlreadyAssignedError(AppError):
    status_code = 409
    code = "ALREADY_ASSIGNED"
    default_detail = "This datasource is already assigned to the client"


class InvalidBillingSourceError(AppError):
    status_code = 400
    code = "INVALID_BILLING_SOURCE"
    default_detail = "Datasource category is not eligible to be a billing source"


class InvalidIdentityAnchorError(AppError):
    status_code = 400
    code = "INVALID_IDENTITY_ANCHOR"
    default_detail = "Datasource category is not eligible to be an identity anchor"


class AssignmentInactiveError(AppError):
    status_code = 400
    code = "ASSIGNMENT_INACTIVE"
    default_detail = "Assignment is inactive"


class InvalidIdentifierError(AppError):
    status_code = 400
    code = "INVALID_IDENTIFIER"
    default_detail = "Identifier type or value is invalid"


class ConnectorNotFoundError(AppError):
    status_code = 404
    code = "CONNECTOR_NOT_FOUND"
    default_detail = "Connector blueprint not found"


class DraftNotFoundError(AppError):
    status_code = 404
    code = "DRAFT_NOT_FOUND"
    default_detail = "Datasource draft not found"


class DatasourceNotFoundError(AppError):
    status_code = 404
    code = "DATASOURCE_NOT_FOUND"
    default_detail = "Datasource not found"


class InvalidDatasourceSelectionError(AppError):
    status_code = 400
    code = "INVALID_DATASOURCE_SELECTION"
    default_detail = "Selected datasources are not valid for this report"


class PreviewExpiredError(AppError):
    status_code = 410
    code = "PREVIEW_EXPIRED"
    default_detail = "Schema preview has expired"


class RequiredMappingMissingError(AppError):
    status_code = 400
    code = "REQUIRED_MAPPING_MISSING"
    default_detail = "Required field mapping is missing"


class SchemaHashMismatchError(AppError):
    status_code = 400
    code = "SCHEMA_HASH_MISMATCH"
    default_detail = "Schema hash does not match the active preview"


class NotImplementedActivationError(AppError):
    status_code = 501
    code = "NOT_IMPLEMENTED"
    default_detail = "Activation for this datasource type is not implemented"


class EmptyResponseError(AppError):
    status_code = 400
    code = "EMPTY_RESPONSE"
    default_detail = "Vendor returned an empty response"


class VendorAuthFailedError(AppError):
    status_code = 400
    code = "VENDOR_AUTH_FAILED"
    default_detail = "Vendor authentication failed"


class InvalidCustomParameterError(AppError):
    status_code = 400
    code = "INVALID_CUSTOM_PARAMETER"
    default_detail = "Invalid custom parameter"


class UpstreamTimeoutError(AppError):
    status_code = 504
    code = "UPSTREAM_TIMEOUT"
    default_detail = "Upstream vendor timed out"


class ReadinessFailedError(AppError):
    status_code = 400
    code = "READINESS_FAILED"
    default_detail = "Report readiness check failed"


class ReportLambdaTimeoutError(AppError):
    status_code = 504
    code = "REPORT_LAMBDA_TIMEOUT"
    default_detail = "Report Lambda timed out"


class ReportLambdaError(AppError):
    status_code = 502
    code = "REPORT_LAMBDA_ERROR"
    default_detail = "Report Lambda returned an error"


class AwsReportCredentialsMissingError(AppError):
    status_code = 500
    code = "AWS_REPORT_CREDENTIALS_MISSING"
    default_detail = "Real AWS credentials for report generation are missing"


class SecretsManagerError(AppError):
    status_code = 502
    code = "SECRETS_MANAGER_ERROR"
    default_detail = "Secrets Manager error"


class S3Error(AppError):
    status_code = 502
    code = "S3_ERROR"
    default_detail = "S3 error"


class DynamoDBError(AppError):
    status_code = 502
    code = "DYNAMODB_ERROR"
    default_detail = "DynamoDB error"


class GlueError(AppError):
    status_code = 502
    code = "GLUE_ERROR"
    default_detail = "Glue error"


class ActivationFailedError(AppError):
    status_code = 500
    code = "ACTIVATION_FAILED"
    default_detail = "Datasource activation failed"


class ActivationBackgroundFailedError(AppError):
    status_code = 500
    code = "ACTIVATION_BACKGROUND_FAILED"
    default_detail = "Background activation failed"


class InvalidCursorError(AppError):
    status_code = 400
    code = "INVALID_CURSOR"
    default_detail = "Pagination cursor is invalid"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(), "code": "VALIDATION_ERROR"},
        )
