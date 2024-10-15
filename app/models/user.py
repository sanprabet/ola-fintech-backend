"""This module defines Pydantic models for user-related data structures."""

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


class ApiResponse(BaseModel):
    """Model for API responses."""
    data: dict
    message: str
    success: bool


class PersonalInfo(BaseModel):
    """Model for personal information."""
    primerNombre: str = Field(..., min_length=1)
    segundoNombre: Optional[str] = Field(None, min_length=1)
    primerApellido: str = Field(..., min_length=1)
    segundoApellido: str = Field(..., min_length=1)
    estadoCivil: str = Field(..., min_length=1)
    fechaNacimiento: str = Field(..., min_length=1)
    genero: str = Field(..., min_length=1)
    nivelEducativo: str = Field(..., min_length=1)
    departamento: str = Field(..., min_length=1)
    ciudad: str = Field(..., min_length=1)


class ProfessionalInfo(BaseModel):
    """Model for professional information."""
    ocupacion: str
    actividadEconomica: str
    estrato: str
    tieneCuentaBancaria: str
    situacionCrediticia: str
    antiguedadTelefonoMovil: str


class UserInformationData(BaseModel):
    """Model for combined user information."""
    personalInfo: PersonalInfo
    professionalInfo: ProfessionalInfo


class BankAccountData(BaseModel):
    """Model for bank account information."""
    accountType: str
    accountNumber: str
    accountInstitution: str


class UserRegisterData(BaseModel):
    """Model for user registration data."""
    uid: Optional[str] = None
    documentType: str
    documentNumber: str
    email: str
    phoneNumber: str


class UserDB(UserRegisterData):
    """Model for user data stored in the database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    uid: str
    admin: Optional[bool] = None
    financialCheck: Optional[str] = None
    personalInfo: Optional[Dict[str, Any]] = None
    professionalInfo: Optional[Dict[str, Any]] = None
    accountInformation: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]):
        """Convert MongoDB document to UserDB instance."""
        if not data:
            return None
        if "_id" in data:
            data["id"] = str(data.pop("_id"))  # Convert MongoDB ObjectId to a string
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert UserDB instance to dictionary."""
        data = self.model_dump(by_alias=True, exclude_none=True)

        # Check if 'id' is present in the data, otherwise provide a fallback
        if "id" in data:
            data["_id"] = str(data.pop("id"))  # Ensure id is converted to a string
        else:
            # Handle the case where id is not present (optional handling)
            data["_id"] = None

        return data
