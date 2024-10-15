"""This module defines the main routes for the credit request API."""

from fastapi import APIRouter, Depends

from app.models.exceptions import CustomError
from app.models.credit import CreditRequestData, ApiResponse
from app.services.user_service import UserService
from app.services.app_service import AppService

router = APIRouter()

def get_user_service() -> UserService:
    """Dependency injection for UserService."""
    return UserService()

def get_app_service() -> AppService:
    """Dependency injection for AppService."""
    return AppService()

@router.get("/credit/{uid}", response_model=ApiResponse)
async def get_active_credit(uid: str, app_service: AppService = Depends(get_app_service))-> ApiResponse:
    """If user has a credit process active, this returns the credit."""
    try:
        status = await app_service.get_credit_status(uid)
        return ApiResponse(
            data={
                "status": status
            },
            message="",
            success=True
        )

    except CustomError as err:
        if err.error_type == "bussiness":
            return ApiResponse(
                data={},
                message=err.message,
                success=False
            )
    except Exception as e:
        raise e


@router.post("/requestCredit", response_model=ApiResponse)
async def request_credit(
    credit: CreditRequestData,
    app_service: AppService = Depends(get_app_service)
) -> ApiResponse:
    """
    Handle credit request.

    Args:
        credit (CreditRequestData): The credit request data.
        app_service (AppService): The application service.

    Returns:
        ApiResponse: The API response object.

    Raises:
        Exception: If an unexpected error occurs.
    """
    try:
        await app_service.create_credit_request(credit)
        return ApiResponse(
            data={},
            message="Tu credito fue solicitado exitosamente.",
            success=True
        )

    except CustomError as err:
        if err.error_type == "bussiness":
            return ApiResponse(
                data={},
                message=err.message,
                success=False
            )
    except Exception as e:
        raise e
