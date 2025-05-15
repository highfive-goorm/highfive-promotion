from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class PromotionBase(BaseModel):
    img_url: str
    start_time: int   # ms timestamp (epoch millis)
    end_time: int     # ms timestamp

class PromotionCreate(PromotionBase):
    pass

class PromotionUpdate(BaseModel):
    img_url: Optional[str]
    start_time: Optional[int]
    end_time: Optional[int]

class PromotionInDB(PromotionBase):
    id: int
