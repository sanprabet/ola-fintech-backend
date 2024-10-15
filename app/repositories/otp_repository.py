"""
This module defines the OTPRepository class for handling OTP-related database operations.
"""

from typing import Dict, Any, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.models.otp import OTPDB, OTPRequest  # Import the OTPDB model

class OTPRepository:
    """Repository class for handling OTP-related database operations."""

    def __init__(self):
        """Initialize the OTPRepository with database connection."""
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DB_NAME]
        self.collection = self.db.otp  # The OTP collection

    async def insert(self, otp: OTPRequest) -> str:
        """Insert a new OTP into the database, ensuring old ones for the same UID are removed."""
        await self.collection.delete_one({"uid": otp["uid"]})
        await self.collection.insert_one(otp)

    async def find_one(self, filter_query: Dict[str, Any]) -> Optional[OTPDB]:
        """Find a single OTP based on the given filter."""
        otp = await self.collection.find_one(filter_query)
        return OTPDB.from_mongo(otp) if otp else None

    async def update(self, otp: OTPDB) -> Optional[OTPDB]:
        """Update an existing OTP in the database."""
        update_data = otp.to_dict()
        del update_data['_id']  # Remove the _id field as it shouldn't be updated
        result = await self.collection.update_one({"_id": ObjectId(otp.id)}, {"$set": update_data})
        if result.modified_count:
            return await self.find_one({"_id": ObjectId(otp.id)})
        return None

    async def delete(self, uid: str) -> bool:
        """Delete an OTP from the database."""
        result = await self.collection.delete_one({"uid": uid})
        return result.deleted_count == 1
