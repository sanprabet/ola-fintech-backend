""" Handle database operations on the collection "messages". """
from typing import List, Optional, Dict, Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.models.message import MessageDB


class MessageRepository:
    """Repository class for handling message-related database operations."""

    def __init__(self):
        """Initialize the MessageRepository with database connection."""
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DB_NAME]
        self.collection = self.db.messages

    async def insert(self, message: MessageDB) -> str:
        """Insert a new message into the database."""
        message_dict = message.to_dict()
        result = await self.collection.insert_one(message_dict)
        return str(result.inserted_id)

    async def find_one(self, filter_query: Dict[str, Any]) -> Optional[MessageDB]:
        """Find a single message based on the given filter."""
        message = await self.collection.find_one(filter_query)
        return MessageDB.from_mongo(message) if message else None

    async def filter_messages(
        self,
        query: Dict[str, Any],
        projection: Dict[str, Any] = None,
        sort: List[tuple] = None,
        skip: int = 0,
        limit: int = 100,
        collation: Dict[str, Any] = None
    ) -> List[MessageDB]:
        """Filter messages based on the given parameters."""
        cursor = self.collection.find(query, projection)

        if sort:
            cursor = cursor.sort(sort)

        if collation:
            cursor = cursor.collation(collation)

        cursor = cursor.skip(skip).limit(limit)

        messages = await cursor.to_list(length=limit)
        return [MessageDB(**message) for message in messages]

    async def update(self, message: MessageDB) -> Optional[MessageDB]:
        """Update an existing message in the database."""
        update_data = message.to_dict()
        del update_data['_id']  # Remove the _id field as it shouldn't be updated
        result = await self.collection.update_one({"_id": ObjectId(message.id)}, {"$set": update_data})
        if result.modified_count:
            return await self.find_one({"_id": ObjectId(message.id)})
        return None

    async def delete(self, message_id: str) -> bool:
        """Delete a message from the database."""
        result = await self.collection.delete_one({"_id": ObjectId(message_id)})
        return result.deleted_count == 1
