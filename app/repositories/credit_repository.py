""" Handle database operations on the collection "credit". """
from typing import List, Optional, Dict, Any
from enum import Enum

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from app.config import settings
from app.models.credit import CreditRequestData, CreditDB

class PyObjectId(ObjectId):
    """Custom ObjectId class for Pydantic models"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        """Custom verifier for ObjectId MongoDB"""
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class StatusEnum(str, Enum):
    """Enumeration of possible credit statuses"""
    PENDING = 'pending'
    REJECTED = 'rejected'
    ACTIVE = 'active'
    PAID = 'paid'
    EXTENDED = 'extended'

class CreditRepository:
    """Repository class for handling credit-related database operations"""

    def __init__(self):
        """Initialize the CreditRepository with database connection"""
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DB_NAME]
        self.collection = self.db.credit

    async def insert(self, credit: CreditRequestData) -> str:
        """Insert a new credit record into the database"""
        credit_dict = credit.model_dump()
        result = await self.collection.insert_one(credit_dict)
        return str(result.inserted_id)

    async def find_one(self, filter_query: Dict[str, Any]) -> Optional[CreditDB]:
        """Find a single credit record based on the given filter"""
        credit = await self.collection.find_one(filter_query)
        return CreditDB(**credit) if credit else None

    async def query(
        self,
        query: Dict[str, Any],
        projection: Dict[str, Any] = None,
        sort: List[tuple] = None,
        skip: int = 0,
        limit: int = 100,
        collation: Dict[str, Any] = None
    ) -> List[CreditDB]:
        """Filter credit records based on the given parameters"""
        cursor = self.collection.find(query, projection)

        if sort:
            cursor = cursor.sort(sort)

        if collation:
            cursor = cursor.collation(collation)

        cursor = cursor.skip(skip).limit(limit)

        credit_list = await cursor.to_list(length=limit)
        return [CreditDB(**credit) for credit in credit_list]

    async def update(self, credit: CreditDB) -> Optional[CreditDB]:
        """Update an existing credit record"""
        update_data = credit.dict(exclude={"id"})  # Exclude id from being updated
        result = await self.collection.update_one(
            {"_id": ObjectId(credit.id)},
            {"$set": update_data}
        )
        if result.modified_count:
            return await self.find_one({"_id": ObjectId(credit.id)})
        return None
