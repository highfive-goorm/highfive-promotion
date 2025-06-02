from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Any
from datetime import datetime

# --- 광고 기본 정보 ---
class AdvertisementBase(BaseModel):
    # id: int = Field(..., description="광고 고유 ID, 관리자가 직접 입력하거나 자동 생성") # 주석처리: MongoDB의 _id를 사용하고, 자동생성 ID는 선택사항
    title: str = Field(..., min_length=1, description="광고 제목")
    img_url: HttpUrl = Field(..., description="광고 이미지 URL")
    description: Optional[str] = Field(None, description="광고 설명")
    start_time: datetime = Field(..., description="광고 시작 시간 (UTC 권장)")
    end_time: datetime = Field(..., description="광고 종료 시간 (UTC 권장)")
    target_product_ids: List[int] = Field(default_factory=list, description="광고 클릭 시 연결될 상품 ID 목록")
    landing_url: Optional[HttpUrl] = Field(None, description="광고 클릭 시 이동할 외부 URL (상품 목록 대신 사용 시)")
    is_active: bool = Field(True, description="광고 활성화 여부 (관리자 제어)")
    # 추가 메타데이터 (예: 광고주 정보, 광고 타입 등)
    metadata: Optional[dict[str, Any]] = Field(None, description="추가 메타데이터")

# --- 광고 생성 시 요청 스키마 ---
class AdvertisementCreate(AdvertisementBase):
    # 생성 시에는 id를 클라이언트가 보내지 않음 (또는 특정 규칙에 따라 생성)
    # id 필드를 직접 관리할 경우 여기에 추가
    # 예: id: int
    pass

# --- 광고 수정 시 요청 스키마 ---
class AdvertisementUpdate(BaseModel):
    title: Optional[str] = None
    img_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    target_product_ids: Optional[List[int]] = None
    landing_url: Optional[HttpUrl] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None

# --- 광고 응답 스키마 (DB에서 읽어온 후) ---
class AdvertisementResponse(AdvertisementBase):
    # MongoDB의 _id를 문자열로 변환하여 사용 (Pydantic v2에서는 model_dump(by_alias=True) 등 활용)
    # 여기서는 간단하게 id 필드를 추가하고, CRUD에서 매핑한다고 가정
    # 또는 실제로는 MongoDB _id를 ObjectId 타입 그대로 사용하거나, 문자열로 변환해서 사용
    mongo_id: str = Field(alias="_id", description="MongoDB 문서 ID") # Pydantic v1 스타일 alias
    id: Optional[int] = Field(None, description="광고 관리용 숫자 ID (선택적)")
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # 이제 Pydantic v2에서는 model_validate(from_attributes=True)
        allow_population_by_field_name = True # _id <-> mongo_id
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

# --- 상품 정보 스키마 (Product Service에서 받아올 데이터 형태 - 예시) ---
class ProductSchema(BaseModel):
    id: int
    name: str
    img_url: Optional[HttpUrl] = None
    price: float
    # ... 기타 필요한 상품 정보

# --- 광고 클릭 시 로깅 서비스로 보낼 데이터 스키마 ---
class AdClickLogData(BaseModel):
    advertisement_id: str # 광고의 mongo_id 또는 관리용 id
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    # ... 기타 필요한 정보