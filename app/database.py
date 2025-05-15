from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient("mongodb://root:mongodb_promotion@mongodb_promotion:27017")
db = client["promotion"]
promotion_collection = db["promotion"]
