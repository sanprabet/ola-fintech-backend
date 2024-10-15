"""This module defines the routes for user-related operations."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from app.models.user import UserRegisterData, ApiResponse, UserInformationData, BankAccountData
from app.services.user_service import UserService
from app.utils.string import decode_url_string

from app.models.exceptions import CustomError

router = APIRouter()

def get_user_service() -> UserService:
    """Dependency injection for UserService."""
    return UserService()

@router.post("/register", response_model=ApiResponse)
async def register(
    user: UserRegisterData,
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse:
    """Register a new user."""
    try:
        user_db = await user_service.register(user)
        return ApiResponse(
            data=user_db.to_dict(),
            message="Tu cuenta ha sido creada correctamente",
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/checkCredentials/{document_number}/{phone_number}/{email}", response_model=ApiResponse)
async def check_credentials(
    document_number: str,
    phone_number: str,
    email: str,
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse:
    """Check if the provided credentials already exist."""
    try:
        phone_exists, document_exists, email_exist = await user_service.check_credentials(
            document_number, phone_number, email
        )
        if phone_exists or document_exists or email_exist:
            error_msg = None
            if phone_exists:
                error_msg = "Este numero de telefono ya está registrado."
            if document_exists:
                error_msg = "Este numero de identificación ya esta registrado."
            if email_exist:
                error_msg = "Este email ya esta registrado."
            if phone_exists and document_exists and email_exist:
                error_msg = "Estas credenciales ya estan registradas con otra cuenta."
            return ApiResponse(data={}, message=error_msg, success=False)
        return ApiResponse(data={}, message="", success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/getEmail/documentNumber/{document_number}", response_model=ApiResponse)
async def get_email(
    document_number: str,
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse:
    """Get user email by document number."""
    try:
        user_email = await user_service.get_email(document_number)

        if not user_email:
            return ApiResponse(
                data={},
                message="El numero de documento y/o contraseña son incorrectos.",
                success=False
            )

        return ApiResponse(data={"email": user_email}, message="", success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/getUser/email/{email_url}", response_model=ApiResponse)
async def get_user_by_email(
    email_url: str,
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse:
    """Get user by email."""
    try:
        email = decode_url_string(email_url)
        user = await user_service.get_user_by_email(email)

        if not user:
            return ApiResponse(
                data={},
                message="No existe un usuario bajo estas credenciales. "
                        "Vuelve a intentar mas tarde o contactanos.",
                success=False
            )

        return ApiResponse(data=user.to_dict(), message="", success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/getUser/uid/{uid}", response_model=ApiResponse)
async def get_user_by_uid(
    uid: str,
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse:
    """Get user by uid."""
    try:
        user = await user_service.get_user_by_uid(uid)

        if not user:
            return ApiResponse(
                data={},
                message="No existe un usuario bajo estas credenciales. "
                        "Vuelve a intentar mas tarde o contactanos.",
                success=False
            )

        user_data = user.to_dict()
        return ApiResponse(data=user_data, message="", success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/sendOtp/uid/{uid}", response_model=ApiResponse)
async def send_otp_code(
    uid: str,
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse:
    """Send OTP code to user and add lock"""
    try:
        await user_service.send_otp(uid)
        return ApiResponse(data={}, message="Código OTP enviado exitosamente", success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/verifyOtp/uid/{uid}/code/{code}", response_model=ApiResponse)
async def verify_otp_code(
    uid: str,
    code: str,
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse:
    """Verify OTP code."""
    try:
        await user_service.verify_otp(uid, code)
        return ApiResponse(data={}, message="Código OTP verificado exitosamente", success=True)
    except CustomError as err:
        return ApiResponse(data={}, message=err.message, success=False)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err)) from err

@router.put("/updateUser", response_model=ApiResponse)
async def add_user_information(
    request: Request,
    data: UserInformationData,
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse:
    """Update user information."""
    try:
        uid = request.query_params.get("uid")
        if not uid:
            raise HTTPException(status_code=400, detail="UID is required")

        updated_user = await user_service.update_user_information(uid, data)
        if updated_user:
            return ApiResponse(
                data=updated_user.to_dict(),
                message="Información del usuario actualizada exitosamente",
                success=True
            )
        return ApiResponse(data={}, message="Usuario no encontrado", success=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.put("/updateBankAccount", response_model=ApiResponse)
async def update_bank_account(
    request: Request,
    data: BankAccountData,
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse:
    """Update user's bank account information."""
    try:
        uid = request.query_params.get("uid")
        if not uid:
            raise HTTPException(status_code=400, detail="UID is required")

        updated_user = await user_service.update_bank_account(uid, data)
        if updated_user:
            return ApiResponse(
                data=updated_user.to_dict(),
                message="Información bancaria actualizada exitosamente",
                success=True
            )
        return ApiResponse(data={}, message="Usuario no encontrado", success=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/updateUserInformation", response_model=ApiResponse)
async def update_user_information(
    request: Request,
    data: UserInformationData,
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse:
    """Update user information."""
    try:
        uid = request.query_params.get("uid")
        if not uid:
            raise HTTPException(status_code=400, detail="UID is required")

        # Uncomment the following line when the method is implemented in user_service
        # updated_user = await user_service.update_user_information(uid, data)
        updated_user = await user_service.add_user_information(uid, data)
        if updated_user:
            return ApiResponse(
                data={},
                message="Información del usuario actualizada exitosamente",
                success=True
            )
        return ApiResponse(data={}, message="Usuario no encontrado", success=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/getUsersAdmin", response_model=ApiResponse)
async def get_all_users_information(
    page: int = Query(1, ge=1),  # page number, minimum value is 1
    limit: int = Query(10, ge=1),  # limit per page, minimum value is 1
    searchTerm: Optional[str] = "",  # search term (empty by default)
    showPending: Optional[bool] = False,  # show only pending users
    showActive: Optional[bool] = False,  # show only active users
    user_service: UserService = Depends(get_user_service)  # Dependency Injection
) -> ApiResponse:
    """Fetch paginated user information, with filtering based on parameters."""
    try:
        # Fetch paginated users from the service based on the filter criteria
        result = await user_service.all_users(
            search_term=searchTerm, 
            show_pending=showPending, 
            show_active=showActive,
            page=page, 
            limit=limit
        )

        formatted_users = [
            {
                "userData": user["user"],               # The user's main data (UserDB)
                "creditHistory": user["credits"],       # The user's credit history (CreditDB[])
                "messageHistory": user["messages"]      # The user's message history (MessageDB[])
            }
            for user in result["users"]
        ]

        # Build the response
        return ApiResponse(
            data={
                "users": formatted_users,
                "total": result["total"]  # Total number of users matching the filters
            },
            message="Información de todos los usuarios obtenida exitosamente",
            success=True
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
