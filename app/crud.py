from .database import promotion_collection
from .schemas import PromotionCreate, PromotionUpdate
from bson import ObjectId

async def create_promotion(promotion: PromotionCreate):
    doc = promotion.dict()
    # id는 auto-increment 처럼 단순 증가(예시, 실서비스면 시퀀스 관리 필요)
    last = await promotion_collection.find_one(sort=[("id", -1)])
    doc["id"] = 1 if not last else last["id"] + 1
    await promotion_collection.insert_one(doc)
    return doc

async def get_promotion(id: int):
    doc = await promotion_collection.find_one({"id": id})
    return doc

async def list_promotions():
    cursor = promotion_collection.find().sort("start_time", -1)
    return [doc async for doc in cursor]

async def update_promotion(id: int, update: PromotionUpdate):
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    result = await promotion_collection.update_one({"id": id}, {"$set": update_data})
    if result.matched_count == 0:
        return None
    return await promotion_collection.find_one({"id": id})

async def delete_promotion(id: int):
    result = await promotion_collection.delete_one({"id": id})
    return result.deleted_count > 0
