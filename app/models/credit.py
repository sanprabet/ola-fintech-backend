"""This module defines Pydantic models and enums for credit-related operations."""

from enum import Enum
from typing import Annotated, Optional, Dict, Any

from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict


class PyObjectId(ObjectId):
    """Custom ObjectId class for Pydantic models."""

    @classmethod
    def __get_validators__(cls):
        """Get validators for PyObjectId."""
        yield cls.validate

    @classmethod
    def validate(cls, v, _field=None):
        """Validate the ObjectId."""
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        """Get JSON schema for PyObjectId."""
        field_schema.update(type="string")


PydanticObjectId = Annotated[PyObjectId, Field(default_factory=PyObjectId, alias="_id")]


class ApiResponse(BaseModel):
    """Model for API responses."""
    data: dict
    message: str
    success: bool


class StatusEnum(str, Enum):
    """Enumeration of possible credit statuses."""
    PENDING = 'pending'
    REJECTED = 'rejected'
    ACTIVE = 'active'
    PAID = 'paid'
    EXTENDED = 'extended'

class ExtensionField(BaseModel):
    """Field of data for when status extended."""
    fechaPago: str
    montoPago: float

class CreditRequestData(BaseModel):
    """Model for credit request data."""
    uid: str
    status: Optional[StatusEnum] = None
    montoSolicitado: float
    interesCorriente: float
    administracion: float
    iva: float
    totalPagar: float
    fechaCuota: str
    otpCode: str
    otpTimeStamp: str

    montoAprobado: Optional[str] = None
    extensionRequested: Optional[bool] = None
    extension: Optional[ExtensionField] = None


class CreditDB(CreditRequestData):
    """Model for credit data stored in the database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    status: StatusEnum

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]):
        """Convert MongoDB document to CreditDB instance."""
        if not data:
            return None
        if "_id" in data:
            data["id"] = data.pop("_id")
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert CreditDB instance to dictionary."""
        data = self.model_dump(by_alias=True, exclude_none=True)
        data["_id"] = str(data["_id"])
        return data
