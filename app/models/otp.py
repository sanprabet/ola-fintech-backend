"""
This module defines Pydantic models for OTP-related data structures.
"""

from typing import Annotated, Dict, Any
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict


class PyObjectId(ObjectId):
    """Custom ObjectId class for Pydantic models."""

    @classmethod
    def __get_validators__(cls):
        """Get validators for PyObjectId."""
        yield cls.validate

    @classmethod
    def validate(cls, v, _values=None, _config=None):
        """Validate the ObjectId."""
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        """Get JSON schema for PyObjectId."""
        field_schema.update(type="string")


PydanticObjectId = Annotated[PyObjectId, Field(default_factory=PyObjectId, alias="_id")]

class OTPRequest(BaseModel):
    """Model for OTP request data."""
    uid: str = Field(..., unique=True)
    code: str = Field(..., min_length=6, max_length=6)
    sentTimeStamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config to ensure datetime is serialized to ISO format by default"""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

class OTPDB(OTPRequest):
    """Model for OTP data stored in the database."""
    id: PydanticObjectId = Field(default_factory=PyObjectId, alias="_id")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]):
        """Convert MongoDB document to OTPDB instance."""
        if not data:
            return None
        if "_id" in data:
            data["id"] = str(data.pop("_id"))  # Convert MongoDB ObjectId to a string
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert OTPDB instance to dictionary."""
        data = self.dict(by_alias=True, exclude_none=True)

        # Check if 'id' is present in the data, otherwise provide a fallback
        if "id" in data:
            data["_id"] = str(data.pop("id"))  # Ensure id is converted to a string
        else:
            data["_id"] = None

        return data
