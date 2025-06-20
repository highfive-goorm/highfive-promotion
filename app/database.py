import os
from dotenv import load_dotenv, find_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(find_dotenv(usecwd=True))

# 기존 MongoDB URI 구성 방식 유지
user = os.getenv('MONGO_USER')
password = os.getenv('MONGO_PASSWORD')
hosts = os.getenv('MONGO_HOSTS')
db_name = os.getenv('MONGO_DB')
replica_set = os.getenv('MONGO_REPLICA_SET')

MONGO_URI = (
    f"mongodb://{user}:{password}@{hosts}/{db_name}?authSource=admin&replicaSet={replica_set}"
)

# 동기 클라이언트 대신 비동기 클라이언트를 사용합니다.
client = AsyncIOMotorClient(MONGO_URI)
db = client[db_name]