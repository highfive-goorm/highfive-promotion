from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue

# Pydantic이 ObjectId를 이해할 수 있도록 만드는 헬퍼 클래스
class PyObjectId(ObjectId):
    @classmethod
    def validate(cls, v):
        """Validate that the input is a valid ObjectId."""
        if not ObjectId.is_valid(v):
            raise ValueError(f"'{v}' is not a valid ObjectId.")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        """
        Return a Pydantic CoreSchema that defines how to validate and serialize ObjectIds.
        Input can be a string or an ObjectId. Output during serialization is a string.
        """
        return core_schema.no_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema_obj: core_schema.CoreSchema, handler) -> JsonSchemaValue:
        """
        Return a JSON schema representation for ObjectId, which is a string.
        """
        # For ObjectId, we simply want to represent it as a string in the OpenAPI schema.
        # 'format: objectid' is a common convention but optional.
        return {'type': 'string', 'format': 'objectid'}


# --- Promotion Schemas ---

class PromotionBase(BaseModel):
    title: str = Field(..., example="나이키 특별 할인")
    description: Optional[str] = Field(None, example="최대 30% 할인!")
    brand_id: int = Field(..., example=101)
    banner_image_url: str = Field(..., example="https://example.com/banner.jpg")
    destination_url: str = Field(..., validation_alias='landing_url', example="/brands/101/new-destination")
    is_active: bool = Field(True, example=True)
    start_date: Optional[datetime] = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None

class PromotionCreate(PromotionBase):
    pass

class PromotionUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    brand_id: Optional[int]
    banner_image_url: Optional[str]
    destination_url: Optional[str]
    is_active: Optional[bool]
    start_date: Optional[datetime]
    end_date: Optional[datetime]

# DB에서 조회한 데이터를 담는 스키마 (API 응답용)
class PromotionInDB(PromotionBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,  # Pydantic V2 style for allowing population by field name (alias)
        json_encoders={ObjectId: str} # Keep for other potential ObjectId fields if any
    )