import httpx # 비동기 HTTP 클라이언트
from typing import List, Optional

from .config import settings
from .schemas import ProductSchema, AdClickLogData

# --- Product Service 연동 ---
async def fetch_products_by_ids(product_ids: List[int]) -> List[ProductSchema]:
    if not product_ids:
        return []
    
    # Product Service의 상품 ID 목록 조회 API가 있다고 가정
    # 예: GET /products/bulk?ids=1&ids=2&ids=3
    # 실제 Product Service의 API 스펙에 맞춰 URL 및 파라미터 조정 필요
    # 여기서는 간단히 product_ids를 쿼리 파라미터로 넘기는 예시
    params = [("product_ids", str(pid)) for pid in product_ids]

    async with httpx.AsyncClient() as client:
        try:
            # Product Service의 bulk 조회 엔드포인트가 있다고 가정 (예: /product/bulk)
            # settings.PRODUCT_SERVICE_URL 은 /product 같은 경로까지 포함할 수도, 루트일 수도 있음.
            # 여기서는 /bulk 엔드포인트를 settings.PRODUCT_SERVICE_URL에 직접 붙이지 않고,
            # product_service/app/main.py의 `/product/bulk`와 같은 특정 경로를 가정합니다.
            # Product Service의 API 스펙에 따라 정확히 맞춰야 합니다.
            # product_service 코드에 있는 /product/bulk 를 사용한다고 가정하면,
            # settings.PRODUCT_SERVICE_URL이 "http://product-service-host" 일 때,
            # 실제 요청 URL은 "http://product-service-host/product/bulk" 가 됩니다.
            # 여기서는 PRODUCT_SERVICE_URL 자체가 /product/bulk 엔드포인트를 가리킨다고 가정하거나,
            # 혹은 더 명확하게 PRODUCT_BULK_ENDPOINT_URL 등을 설정 파일에 추가합니다.
            # 아래는 settings.PRODUCT_SERVICE_URL이 'http://<product_service>/product' 이고, bulk API가 '/bulk'에 있다고 가정
            # 실제 Product 서비스의 `/product/bulk` 엔드포인트가 `product_ids`를 `List[int]` 형태의 JSON body로 받는다고 가정
            product_service_bulk_url = f"{settings.PRODUCT_SERVICE_URL.rstrip('/')}/bulk" # Product Service의 bulk API 경로
            response = await client.post(product_service_bulk_url, json={"product_ids": product_ids})
            response.raise_for_status() # 2xx 외 상태 코드면 예외 발생
            products_data = response.json() # 응답이 List[ProductSchema] 형태라고 가정
            # Pydantic 모델로 변환 (응답이 이미 ProductSchema 리스트 형태면 생략 가능)
            return [ProductSchema(**prod) for prod in products_data]
        except httpx.HTTPStatusError as e:
            print(f"HTTP error calling Product Service: {e.response.status_code} - {e.response.text}")
            return [] # 또는 예외를 다시 발생시켜 상위 핸들러에서 처리
        except Exception as e:
            print(f"Error calling Product Service: {e}")
            return []

# --- Logging Service 연동 (아직 Logging Service가 없으므로 주석 또는 임시 로직) ---
async def send_ad_click_log(log_data: AdClickLogData):
    # 실제 Logging Service API가 준비되면 여기에 구현
    # 예: POST /logs/advertisement-click
    logging_service_endpoint = f"{settings.LOGGING_SERVICE_URL.rstrip('/')}/advertisement-click" # 로깅 서비스의 광고 클릭 로그 엔드포인트 (예시)
    
    async with httpx.AsyncClient() as client:
        try:
            # 로깅 서비스는 보통 201 또는 204를 반환하고 특별한 응답 바디가 없을 수 있음
            response = await client.post(logging_service_endpoint, json=log_data.model_dump())
            response.raise_for_status() # 로깅 실패 시 에러 발생 (선택적, 로깅 실패가 주 서비스에 영향을 주지 않게 하려면 예외 처리)
            print(f"Successfully sent ad click log to Logging Service: {log_data.advertisement_id}")
            return True
        except httpx.HTTPStatusError as e:
            print(f"HTTP error sending log to Logging Service: {e.response.status_code} - {e.response.text}")
            # 로깅 실패는 주 흐름에 영향을 주지 않도록 처리하는 것이 일반적
            return False
        except Exception as e:
            print(f"Error sending log to Logging Service: {e}")
            return False