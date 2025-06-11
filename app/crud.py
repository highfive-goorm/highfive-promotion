from bson import ObjectId
from datetime import datetime
from typing import List

from .database import db
from .schemas import PromotionCreate, PromotionUpdate

promotion_collection = db["promotion"]

# --- 비동기 Promotion CRUD ---

async def create_promotion(promotion: PromotionCreate) -> dict:
    promotion_data = promotion.dict()
    now = datetime.utcnow()
    promotion_data["created_at"] = now
    promotion_data["updated_at"] = now
    result = await promotion_collection.insert_one(promotion_data)
    created_promotion = await promotion_collection.find_one({"_id": result.inserted_id})
    return created_promotion

async def get_promotion(promotion_id: str) -> dict:
    promotion = await promotion_collection.find_one({"_id": ObjectId(promotion_id)})
    return promotion

async def get_active_promotions(skip: int = 0, limit: int = 10) -> List[dict]:
    now = datetime.utcnow()
    query = {
        "is_active": True,
        "start_date": {"$lte": now},
        "$or": [
            {"end_date": None},
            {"end_date": {"$gte": now}}
        ]
    }
    cursor = promotion_collection.find(query).skip(skip).limit(limit)
    promotions = await cursor.to_list(length=limit)
    return promotions

async def update_promotion(promotion_id: str, promotion_update: PromotionUpdate) -> dict:
    update_data = promotion_update.dict(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await promotion_collection.update_one(
            {"_id": ObjectId(promotion_id)}, {"$set": update_data}
        )
    updated_promotion = await get_promotion(promotion_id)
    return updated_promotion

async def delete_promotion(promotion_id: str) -> bool:
    """프로모션을 삭제하고 성공 여부를 bool 값으로 반환합니다."""
    result = await promotion_collection.delete_one({"_id": ObjectId(promotion_id)})
    return result.deleted_count > 0