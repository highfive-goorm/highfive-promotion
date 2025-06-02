import os
from dotenv import load_dotenv, find_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

# .env 파일에서 환경 변수 로드
# find_dotenv(usecwd=True)는 현재 작업 디렉토리부터 상위로 .env를 찾음
# promotion_service 디렉토리 내에서 실행된다면 해당 디렉토리의 .env를 찾을 것임
load_dotenv(find_dotenv(usecwd=True))

# 기존 MongoDB URI 구성 방식 유지
MONGO_URI = (
    f"mongodb://{os.getenv('DB_USER')}:{os.getenv('MONGO_PASSWORD')}"
    f"@{os.getenv('MONGO_URL')}:{os.getenv('MONGO_PORT')}"
    f"/{os.getenv('MONGO_DB')}?authSource=admin"
)

# 데이터베이스 이름도 환경 변수에서 가져옴 (기존 'MONGO_DB')
DB_NAME = os.getenv('MONGO_DB') # 'product' 데이터베이스를 사용

# 프로모션 정보를 저장할 컬렉션 이름 (고정값 또는 환경 변수)
ADVERTISEMENT_COLLECTION_NAME = "promotion" # 전임자가 설정한 컬렉션 이름

client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None
advertisement_collection: AsyncIOMotorCollection = None # 컬렉션 객체도 전역으로 관리 (선택적)

async def connect_to_mongo():
    global client, db, advertisement_collection
    if client and db and advertisement_collection: # 이미 연결되어 있다면 재연결 방지
        print("MongoDB connection already established for Promotion Service.")
        return

    print(f"Connecting to Promotion MongoDB at {os.getenv('MONGO_URL')}:{os.getenv('MONGO_PORT')} with DB: {DB_NAME}...")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME] # 'product' 데이터베이스 사용
    advertisement_collection = db[ADVERTISEMENT_COLLECTION_NAME] # 'promotion' 컬렉션 사용

    try:
        await client.admin.command('ping')
        print("Successfully connected to Promotion MongoDB (using 'product' DB, 'promotion' collection).")
        # 인덱스 생성 (애플리케이션 시작 시) - advertisement_collection 객체 사용
        await advertisement_collection.create_index(
            [("is_active", 1), ("start_time", 1), ("end_time", 1)],
            name="idx_active_time_promotion" # 인덱스 이름 지정
        )
        # 광고 ID를 관리하고 고유하게 사용한다면 (예: 숫자 ID 필드)
        # await advertisement_collection.create_index([("advertisement_numeric_id", 1)], unique=True, sparse=True, name="idx_numeric_id_promotion")
        # 만약 MongoDB 자체 _id 외에 별도의 'id' 필드를 사용하고 unique하게 관리한다면
        # await advertisement_collection.create_index([("id", 1)], unique=True, sparse=True, name="idx_custom_id_promotion")

    except Exception as e:
        print(f"Failed to connect to Promotion MongoDB or create indexes: {e}")
        client = None # 연결 실패 시 None으로 설정
        db = None
        advertisement_collection = None
        raise

async def close_mongo_connection():
    global client
    if client:
        client.close()
        client = None # 닫힌 후 None으로 설정
        db = None
        advertisement_collection = None
        print("Promotion MongoDB connection closed.")

# 컬렉션 객체를 직접 반환하는 함수 (crud.py 등에서 사용)
def get_advertisement_collection() -> AsyncIOMotorCollection:
    if advertisement_collection is None:
        # 이 경우는 connect_to_mongo가 호출되지 않았거나 실패한 경우
        # 실제 운영 환경에서는 더 견고한 처리가 필요합니다.
        # 예: 애플리케이션 시작 시 연결 실패면, 요청 처리 전에 에러 발생
        raise RuntimeError("Advertisement collection not initialized. Call connect_to_mongo first in Promotion Service.")
    return advertisement_collection