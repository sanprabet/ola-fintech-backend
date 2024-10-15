"""This module contains the UserRepository class for database operations on user data."""

from typing import List, Optional, Dict, Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.models.user import UserRegisterData, UserDB

class UserRepository:
    """Repository class for handling user-related database operations."""

    def __init__(self):
        """Initialize the UserRepository with database connection."""
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DB_NAME]
        self.collection = self.db.users

    async def insert(self, user: UserRegisterData) -> str:
        """Insert a new user into the database."""
        user_dict = user.model_dump()
        result = await self.collection.insert_one(user_dict)
        return str(result.inserted_id)

    async def find_one(self, filter_query: Dict[str, Any]) -> Optional[UserDB]:
        """Find a single user based on the given filter."""
        user = await self.collection.find_one(filter_query)
        return UserDB.from_mongo(user) if user else None

    async def filter_users(
        self,
        query: Dict[str, Any],
        projection: Dict[str, Any] = None,
        sort: List[tuple] = None,
        skip: int = 0,
        limit: int = 100,
        collation: Dict[str, Any] = None
    ) -> List[UserDB]:
        """Filter users based on the given parameters."""
        cursor = self.collection.find(query, projection)

        if sort:
            cursor = cursor.sort(sort)

        if collation:
            cursor = cursor.collation(collation)

        cursor = cursor.skip(skip).limit(limit)

        users = await cursor.to_list(length=limit)
        return [UserDB(**user) for user in users]

    async def update(self, user: UserDB) -> Optional[UserDB]:
        """Update an existing user in the database."""
        update_data = user.to_dict()
        del update_data['_id']  # Remove the _id field as it shouldn't be updated
        result = await self.collection.update_one({"_id": ObjectId(user.id)}, {"$set": update_data})
        if result.modified_count:
            return await self.find_one({"_id": ObjectId(user.id)})
        return None
