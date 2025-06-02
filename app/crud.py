from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId # MongoDB의 ObjectId 사용 시
from datetime import datetime, timezone
from typing import List, Optional

from .database import get_promotion_collection, ADVERTISEMENT_COLLECTION
from .schemas import AdvertisementCreate, AdvertisementUpdate, AdvertisementResponse

# --- Helper function to convert MongoDB doc to Pydantic model ---
# Pydantic v2 에서는 AdvertisementResponse.model_validate(doc) 로 더 간단하게 가능
def advertisement_helper(advertisement_doc) -> dict:
    # ObjectId를 문자열로 변환
    if "_id" in advertisement_doc and isinstance(advertisement_doc["_id"], ObjectId):
        advertisement_doc["_id"] = str(advertisement_doc["_id"])

    # 모든 datetime 필드를 UTC로 가정하거나, timezone 정보가 없다면 추가
    for key, value in advertisement_doc.items():
        if isinstance(value, datetime) and value.tzinfo is None:
            advertisement_doc[key] = value.replace(tzinfo=timezone.utc)
    return advertisement_doc


# --- 광고 CRUD 함수 ---
async def create_advertisement(ad_data: AdvertisementCreate) -> dict:
    collection: AsyncIOMotorCollection = get_promotion_collection(ADVERTISEMENT_COLLECTION)
    ad_dict = ad_data.model_dump(exclude_unset=True)
    now = datetime.now(timezone.utc)
    ad_dict["created_at"] = now
    ad_dict["updated_at"] = now
    # 만약 관리용 숫자 ID를 자동 증가 등으로 생성한다면 여기서 로직 추가
    # 예: counter 컬렉션을 사용하거나, 마지막 ID 조회 후 +1

    result = await collection.insert_one(ad_dict)
    created_ad = await collection.find_one({"_id": result.inserted_id})
    return advertisement_helper(created_ad) if created_ad else None

async def get_advertisement_by_id(ad_mongo_id: str) -> Optional[dict]:
    collection: AsyncIOMotorCollection = get_promotion_collection(ADVERTISEMENT_COLLECTION)
    try:
        obj_id = ObjectId(ad_mongo_id) # 문자열 ID를 ObjectId로 변환
    except Exception:
        return None # 유효하지 않은 ObjectId 형식
    ad = await collection.find_one({"_id": obj_id})
    return advertisement_helper(ad) if ad else None

async def get_active_advertisements(limit: int = 10, skip: int = 0) -> List[dict]:
    collection: AsyncIOMotorCollection = get_promotion_collection(ADVERTISEMENT_COLLECTION)
    now = datetime.now(timezone.utc)
    query = {
        "is_active": True,
        "start_time": {"$lte": now},
        "end_time": {"$gte": now}
    }
    ads_cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
    active_ads = []
    async for ad_doc in ads_cursor:
        active_ads.append(advertisement_helper(ad_doc))
    return active_ads

async def update_advertisement(ad_mongo_id: str, ad_data: AdvertisementUpdate) -> Optional[dict]:
    collection: AsyncIOMotorCollection = get_promotion_collection(ADVERTISEMENT_COLLECTION)
    try:
        obj_id = ObjectId(ad_mongo_id)
    except Exception:
        return None

    update_data = ad_data.model_dump(exclude_unset=True) # 업데이트할 필드만 포함
    if not update_data:
        return await get_advertisement_by_id(ad_mongo_id) # 변경사항 없으면 현재 데이터 반환

    update_data["updated_at"] = datetime.now(timezone.utc)

    result = await collection.update_one({"_id": obj_id}, {"$set": update_data})
    if result.matched_count > 0:
        updated_ad = await collection.find_one({"_id": obj_id})
        return advertisement_helper(updated_ad) if updated_ad else None
    return None

async def delete_advertisement(ad_mongo_id: str) -> bool:
    collection: AsyncIOMotorCollection = get_promotion_collection(ADVERTISEMENT_COLLECTION)
    try:
        obj_id = ObjectId(ad_mongo_id)
    except Exception:
        return False
    result = await collection.delete_one({"_id": obj_id})
    return result.deleted_count > 0