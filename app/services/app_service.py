"""Module for handling all the admin and user app interactions"""
from datetime import datetime, timedelta

from typing import Optional

from app.models.credit import CreditRequestData, CreditDB
from app.models.exceptions import CustomError
from app.repositories.user_repository import UserRepository
from app.repositories.credit_repository import CreditRepository

class AppService:
    """Service class for handling application logic related to credit requests."""

    def __init__(self):
        """Initialize AppService with user and credit repositories."""
        self.user_repository = UserRepository()
        self.credit_repository = CreditRepository()

    async def get_credit(self, uid: str) -> Optional[CreditDB]:
        """
        Check and return current credit data

        Args:
            uid (string): User Firebase Id

        Raises:
            CustomError:

        Returns:
            str: The status
        """

        active_credit = await self.credit_repository.find_one({
            "uid": uid,
            "$or":[
                {"status": "active"},
                {"status": "pending"},
                {"status": "extended"},
            ]
        })

        if active_credit:
            return active_credit

        six_months_ago = datetime.now() - timedelta(days=180)
        six_months_ago_str = six_months_ago.isoformat()
        rejected_credit = await self.credit_repository.find_one({
            "uid": uid,
            "status": "rejected",
            "otpTimeStamp": {"$gte": six_months_ago_str}
        })

        if rejected_credit:
            return rejected_credit



    async def create_credit_request(self, credit: CreditRequestData):
        """
        Create a credit request for a user.

        Args:
            credit (CreditRequestData): The credit request data.

        Raises:
            CustomError: If the user has an active credit or a recent rejected request.

        Returns:
            str: The ID of the inserted credit request.
        """

        is_active_or_pending = await self.credit_repository.find_one({
            "uid": credit.uid,
            "$or": [
                {"status":"active"},
                {"status":"pending"}
            ]
        })

        if is_active_or_pending:
            raise CustomError(
                "Ya tienes un credito/peiticion activa.",
                "bussiness"
            )

        six_months_ago = datetime.now() - timedelta(days=180)
        six_months_ago_str = six_months_ago.isoformat()
        rejected_recent = await self.credit_repository.find_one({
            "uid": credit.uid,
            "status": "rejected",
            "otpTimeStamp": {"$gte": six_months_ago_str}
        })

        if rejected_recent:
            raise CustomError("Debes esperar 6 meses para pedir tu crédito.", "bussiness")

        credit.status = "pending"
        await self.credit_repository.insert(credit)



    async def request_extension_credit_payment(self, uid: str):
        """ Update extensionRequested field on credit """
        active_credit = await self.credit_repository.find_one({
            "uid": uid,
            "status": "active"
        })

        if active_credit:
            fecha_cuota_str = active_credit.fechaCuota
            fecha_cuota = datetime.strptime(fecha_cuota_str, "%d/%m/%Y")

            yesterday = datetime.now() - timedelta(days=1)

            if fecha_cuota <= yesterday:
                raise CustomError("Este credito no es valido para pedir extension de cupo", "bussiness")

            active_credit.extensionRequested = True

            await self.credit_repository.update(active_credit)
        else:
            raise CustomError("Este usuario no tiene un credito activo", "bussiness")
