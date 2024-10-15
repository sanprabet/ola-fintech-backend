"""
This module defines models for managing message data in the system, 
including Twilio message details and database storage for messages.
"""

from enum import Enum
from typing import Annotated, Optional, Dict, Any
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict


class PyObjectId(ObjectId):
    """
    Custom ObjectId class for Pydantic models.
    This class provides a mechanism to validate and handle MongoDB ObjectId types.
    """

    @classmethod
    def __get_validators__(cls):
        """Yield validator methods for PyObjectId."""
        yield cls.validate

    @classmethod
    def validate(cls, v, _field=None):
        """Validate if the value is a valid ObjectId."""
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        """Get JSON schema for PyObjectId."""
        field_schema.update(type="string")

PydanticObjectId = Annotated[PyObjectId, Field(default_factory=PyObjectId, alias="_id")]

class MessageStatusEnum(str, Enum):
    """
    Enumeration of possible message statuses.
    This enum defines the different states a message can be in, such as 'pending', 'sent', or 'failed'.
    """
    PENDING = 'pending'
    SENT = 'sent'
    ERROR = 'error'
    SCHEDULED = 'scheduled'
    FAILED = 'failed'

class SentDetails(BaseModel):
    """Model for message sent details."""
    sid: str  # Twilio Message SID
    dateCreated: Optional[str] = None  # When the message was created
    dateQueued: Optional[str] = None  # When the message was queued for sending
    dateSent: Optional[str] = None  # When the message was sent (might not be available if still queued)
    to: str  # Recipient's phone number
    from_: Optional[str] = Field(None, alias='from')
    body: str  # Message content
    status: str  # Message status (queued, sent, delivered, failed, etc.)
    numSegments: Optional[str] = None  # Number of message segments
    numMedia: Optional[str] = None  # Number of media attachments
    direction: Optional[str] = None  # Message direction (outbound/inbound)
    price: Optional[str] = None  # Cost of sending the message (if available)
    priceUnit: Optional[str] = None  # Currency used for the price
    errorCode: Optional[str] = None  # Error code if the message failed
    errorMessage: Optional[str] = None  # Error message if the message failed
    uri: Optional[str] = None  # URI of the message resource
    subresourceUris: Optional[dict] = None  # Links to related resources (e.g., media)

    class Config:
        """Pydantic model configuration."""
        orm_mode = True
        allow_population_by_field_name = True
        extra = "allow"


class MessageDB(BaseModel):
    """
    Model for storing message-related data in the database.
    This includes user-specific information, message status, scheduling, retries, errors, and metadata.
    """
    id: PydanticObjectId = Field(default_factory=PyObjectId, alias="_id")  # MongoDB ObjectId
    uid: str  # The user ID associated with the message
    messageType: str = Field(..., description="Type of message: SMS, WhatsApp, Email")  # Message type
    status: MessageStatusEnum  # Unified message status (pending, sent, error, etc.)

    scheduledTimeStamp: Optional[str] = None  # When the message is scheduled to be sent
    retryCount: int = Field(default=0, description="Number of retries attempted")  # Retry count for failed messages
    sent: Optional[SentDetails] = None  # The Twilio or message-sending details
    error: Optional[Dict[str, str]] = None  # Top-level error if the message fails
    meta: Optional[Dict[str, Any]] = None  # Optional metadata like priority, tags, etc.

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]):
        """
        Convert MongoDB document to MessageDB instance.
        This method transforms a MongoDB document into an instance of the MessageDB class.
        """
        if not data:
            return None
        if "_id" in data:
            data["id"] = data.pop("_id")
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert MessageDB instance to a dictionary.
        This method serializes the MessageDB instance into a dictionary format.
        """
        return self.dict(by_alias=True)
