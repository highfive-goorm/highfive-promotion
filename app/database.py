import os
from dotenv import load_dotenv, find_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(find_dotenv(usecwd=True))

# 기존 MongoDB URI 구성 방식 유지
MONGO_URI = (
    f"mongodb://{os.getenv('DB_USER')}:{os.getenv('MONGO_PASSWORD')}"
    f"@{os.getenv('MONGO_URL')}:{os.getenv('MONGO_PORT')}"
    f"/{os.getenv('MONGO_DB')}?authSource=admin"
)

# 데이터베이스 이름도 환경 변수에서 가져옴 (기존 'MONGO_DB')
DB_NAME = os.getenv('MONGO_DB') # 'product' 데이터베이스를 사용

# 동기 클라이언트 대신 비동기 클라이언트를 사용합니다.
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]