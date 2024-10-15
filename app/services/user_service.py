""" This module manage everything related to user processes """
import random
from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime

from twilio.base.exceptions import TwilioRestException

from app.models.user import UserRegisterData, UserDB, UserInformationData, BankAccountData
from app.models.credit import CreditDB
from app.models.message import MessageDB

from app.models.exceptions import CustomError

from app.repositories.user_repository import UserRepository
from app.repositories.credit_repository import CreditRepository
from app.repositories.msg_repository import MessageRepository
from app.repositories.twilio_repository import TwilioRepository
from app.repositories.otp_repository import OTPRepository


class UserService:
    """Service class for handling user-related operations."""

    def __init__(self):
        """Initialize UserService with necessary repositories."""
        self.user_repository = UserRepository()
        self.credit_repository = CreditRepository()
        self.message_repository = MessageRepository()
        self.otp_repository = OTPRepository()
        self.twilio_repository = TwilioRepository()

    async def register(self, user: UserRegisterData) -> Optional[UserDB]:
        """Register a new user and return the created user."""
        await self.user_repository.insert(user)
        return await self.user_repository.find_one({"documentNumber": user.documentNumber})

    async def get_user_by_email(self, email: str) -> Optional[UserDB]:
        """Retrieve a user by their email address."""
        return await self.user_repository.find_one({"email": email})

    async def get_user_by_uid(self, uid: str) -> Optional[UserDB]:
        """Retrieve a user by their UID."""
        return await self.user_repository.find_one({"uid": uid})

    async def check_credentials(self, document_number: str, phone_number: str, email: str) -> Tuple[bool, bool, bool]:
        """Check if the provided credentials already exist (phone, document, and email)."""
        checks = await self.user_repository.filter_users({
            "$or": [
                {"phoneNumber": phone_number},
                {"documentNumber": document_number},
                {"email": email}
            ]
        })
        phone_exists = any(user.phoneNumber == phone_number for user in checks)
        document_exists = any(user.documentNumber == document_number for user in checks)
        email_exists = any(user.email == email for user in checks)
        return phone_exists, document_exists, email_exists

    async def get_email(self, document_number: str) -> Optional[str]:
        """Retrieve a user's email by their document number."""
        user_db = await self.user_repository.find_one({"documentNumber": document_number})
        return user_db.email if user_db else None

    async def update_user_information(self, uid: str, data: UserInformationData) -> Optional[UserDB]:
        """Add or update user information."""
        user_db = await self.user_repository.find_one({"uid": uid})
        if user_db:
            user_db.personalInfo = data.personalInfo.model_dump()
            user_db.professionalInfo = data.professionalInfo.model_dump()
            return await self.user_repository.update(user_db)
        return None

    async def update_bank_account(self, uid: str, data: BankAccountData) -> Optional[UserDB]:
        """Update user's bank account information."""
        user_db = await self.user_repository.find_one({"uid": uid})
        if user_db:
            user_db.accountInformation = data.model_dump()
            return await self.user_repository.update(user_db)
        return None

    async def send_otp(self, uid: str) -> bool:
        """Generate and send an OTP to the user's phone number."""
        try:
            user_db = await self.user_repository.find_one({"uid": uid})
            if not user_db:
                raise CustomError("Theres no credentials in this request.", "invalid")

            otp_code = str(random.randint(100000, 999999))
            otp_msg = f"Tu codigo de ingreso de Ola Fintech es {otp_code}"

            await self.twilio_repository.send_sms(user_db.phoneNumber, otp_msg)

            otp_data = {
                "uid": user_db.uid,
                "code": otp_code,
                "sentTimeStamp": datetime.utcnow()
            }
            await self.otp_repository.insert(otp_data)

            return True

        except TwilioRestException as e:
            print(f"Error when sending msg: {e}")
        except ValueError as e:
            print(f"Invalid phone number or OTP format: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    async def verify_otp(self, uid: str, code: str):
        """Verify the OTP code provided by the user."""

        current_code = await self.otp_repository.find_one({"uid": uid})

        if not current_code:
            raise CustomError("Pide un nuevo codigo, intenta de nuevo.", "invalid")


        if current_code.code != code:
            raise CustomError("El código es incorrecto, intenta de nuevo.", "invalid")

        await self.otp_repository.delete(uid)


    async def all_users(
        self,
        search_term: Optional[str] = "",
        show_pending: Optional[bool] = False,
        show_active: Optional[bool] = False,
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Fetch paginated users with filters for pending/active status and search term."""

        # Build the query to exclude admin users and apply search filters
        query = self._build_user_query(search_term, show_pending, show_active)

        # Calculate the skip value for pagination
        skip = (page - 1) * limit

        # Fetch the total number of users matching the query
        total_users = await self.user_repository.collection.count_documents(query)

        # Fetch the users with pagination applied (skip and limit)
        users = await self.user_repository.filter_users(query=query, skip=skip, limit=limit)

        # Enrich user data with associated credits and messages
        users_with_related_data = await self._add_related_data_to_users(users)

        return {
            "total": total_users,
            "users": users_with_related_data
        }

    def _build_user_query(self, search_term: str, show_pending: bool, show_active: bool) -> Dict[str, Any]:
        """Build a query to filter users based on search term and status."""
        # Query for users where 'admin' is either False or the field doesn't exist
        query = {
            "$or": [
                {"admin": False},
                {"admin": {"$exists": False}}
            ]
        }

        # Apply search filters based on username, email, or document number
        if search_term:
            query["$and"] = [
                query,  # Maintain the 'admin' condition
                {
                    "$or": [
                        {"username": {"$regex": search_term, "$options": "i"}},
                        {"email": {"$regex": search_term, "$options": "i"}},
                        {"documentNumber": {"$regex": search_term, "$options": "i"}}
                    ]
                }
            ]

        # Apply filters for status if needed
        if show_pending:
            query["status"] = "pending"
        elif show_active:
            query["status"] = "active"

        return query

    async def _add_related_data_to_users(self, users: List[UserDB]) -> List[Dict[str, Any]]:
        """Enrich each user with associated credits and messages."""
        users_with_related_data = []
        
        for user in users:
            uid = user.uid


            # Await the coroutine and log the data retrieved
            credits_data = await self.credit_repository.query({"uid": uid})
            messages_data = await self.message_repository.filter_messages({"uid": uid})
            # Safeguard - ensure that credits_data is a list of dicts or CreditDB instances
            credit = [
                credit if isinstance(credit, CreditDB) else CreditDB(**credit) 
                for credit in credits_data
            ]

            # Assuming messages_data is a list of dictionaries
            msg = [MessageDB(**message) for message in messages_data]

            # Append the enriched data for each user and log the final output
            enriched_data = {
                "user": user,
                "credits": credit if credit else [],  # Assuming credits_data is a list of dicts or CreditDB instances
                "messages": msg if msg else []  # Assuming messages is a list of dicts
            }
            
            users_with_related_data.append(enriched_data)

        return users_with_related_data
