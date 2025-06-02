import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Promotion Service"
    PROJECT_VERSION: str = "0.1.0"

    # 외부 서비스 URL (환경 변수에서 가져옴)
    PRODUCT_SERVICE_URL: str = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8001/api/v1/products") # 예시 URL
    LOGGING_SERVICE_URL: str = os.getenv("LOGGING_SERVICE_URL", "http://localhost:8002/api/v1/logs") # 예시 URL

settings = Settings()