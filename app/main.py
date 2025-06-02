from fastapi import FastAPI, HTTPException, Depends, Query, Path, status, Request
from typing import List, Optional
import logging
import os

from .database import connect_to_mongo, close_mongo_connection
from .schemas import (
    AdvertisementCreate, AdvertisementUpdate, AdvertisementResponse,
    ProductSchema, AdClickLogData
)
from . import crud
from . import services
from .config import settings # 설정 가져오기

# 로깅 설정
LOG_DIR_MAIN = os.path.join(os.getcwd(), "logs") # main.py에서도 로그 디렉토리 생성 (중복될 수 있으나 안전하게)
os.makedirs(LOG_DIR_MAIN, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR_MAIN, "promotion_service.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Manages advertisements and their interactions."
)

# --- Event Handlers ---
@app.on_event("startup")
async def startup_event():
    logger.info(f"{settings.PROJECT_NAME} is starting up...")
    await connect_to_mongo()
    logger.info(f"Product Service URL: {settings.PRODUCT_SERVICE_URL}")
    logger.info(f"Logging Service URL: {settings.LOGGING_SERVICE_URL}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"{settings.PROJECT_NAME} is shutting down...")
    await close_mongo_connection()

# --- Middleware (선택적: 요청 로깅 등) ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response


# --- API Endpoints ---

# 광고 목록 조회 (활성화된 광고)
@app.get("/advertisements/active", response_model=List[AdvertisementResponse], summary="활성화된 광고 목록 조회")
async def list_active_advertisements(
    limit: int = Query(10, ge=1, le=100, description="가져올 광고 수"),
    skip: int = Query(0, ge=0, description="건너뛸 광고 수 (페이징용)")
):
    """
    현재 시간 기준으로 노출 가능한 활성화된 광고 목록을 반환합니다.
    최신 생성된 광고 순으로 정렬됩니다.
    """
    active_ads_docs = await crud.get_active_advertisements(limit=limit, skip=skip)
    if not active_ads_docs:
        return []
    # Pydantic 모델로 변환 (crud 함수가 dict를 반환한다고 가정)
    return [AdvertisementResponse.model_validate(ad) for ad in active_ads_docs] # Pydantic v2
    # Pydantic v1: return [AdvertisementResponse(**ad) for ad in active_ads_docs]


# 광고 클릭 시 연결될 상품 목록 조회 또는 랜딩 URL 제공
@app.get("/advertisements/{ad_id}/landing", summary="광고 클릭 시 랜딩 정보 조회")
async def get_advertisement_landing_info(
    ad_id: str = Path(..., description="광고의 MongoDB ID (_id)")
):
    """
    특정 광고를 클릭했을 때 사용자를 안내할 정보를 반환합니다.
    landing_url이 설정되어 있으면 해당 URL을,
    아니면 target_product_ids에 해당하는 상품 목록을 반환합니다.
    """
    ad_doc = await crud.get_advertisement_by_id(ad_id)
    if not ad_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="광고를 찾을 수 없습니다.")
    
    advertisement = AdvertisementResponse.model_validate(ad_doc) # Pydantic v2

    # 클릭 로그 전송 (비동기적으로, 실패해도 주 기능에 영향 없도록)
    # 실제로는 프론트엔드가 광고 클릭 후 이 API를 호출하기 전에
    # 별도의 /advertisements/{ad_id}/click 같은 API를 호출하여 로그를 남기는 것이 더 일반적입니다.
    # 여기서는 랜딩 정보 조회 시점에 로그를 남긴다고 가정하거나,
    # 또는 이 API의 목적을 "랜딩 정보 조회"로만 한정하고, 클릭 로깅은 별도 API로 분리합니다.
    # 아래는 클릭 로깅을 별도 API로 분리하는 것을 권장하며, 여기서는 주석 처리합니다.
    """
    log_payload = AdClickLogData(
        advertisement_id=advertisement.mongo_id,
        # user_id, session_id 등은 요청 헤더나 다른 방식으로 전달받아 채워야 함
    )
    async def log_task(): # 비동기 백그라운드 작업처럼
        await services.send_ad_click_log(log_payload)
    # FastAPI의 BackgroundTasks를 사용하거나, asyncio.create_task 등으로 실행 가능
    # request.app.state.background_tasks.add_task(log_task) # 예시
    # 또는 그냥 await services.send_ad_click_log(log_payload) (응답 지연 가능성)
    """

    if advertisement.landing_url:
        return {"type": "url", "url": str(advertisement.landing_url)}
    
    if advertisement.target_product_ids:
        products = await services.fetch_products_by_ids(advertisement.target_product_ids)
        if not products: # Product Service에서 상품을 못 찾거나 오류 발생 시
             # 광고는 있지만 연결된 상품이 없는 경우, 어떻게 처리할지 정책 필요
             # 예: 빈 상품 목록 반환 또는 특정 메시지 반환
            logger.warning(f"No products found for ad_id {ad_id} with target_product_ids: {advertisement.target_product_ids}")
            # return {"type": "products", "products": [], "message": "연결된 상품 정보를 가져오지 못했습니다."}

        return {"type": "products", "products": products}
    
    # landing_url도 없고 target_product_ids도 없는 경우
    logger.warning(f"Advertisement {ad_id} has no landing_url and no target_product_ids.")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="광고에 연결된 상품 정보나 랜딩 URL이 없습니다.")


# (핵심) 광고 클릭 로그 기록 위임 API
@app.post("/advertisements/{ad_id}/click", status_code=status.HTTP_202_ACCEPTED, summary="광고 클릭 이벤트 로깅 위임")
async def record_advertisement_click(
    ad_id: str = Path(..., description="클릭된 광고의 MongoDB ID (_id)"),
    # user_id 등은 실제로는 인증 시스템을 통해 헤더에서 가져오거나, 프론트에서 바디로 전달
    user_id: Optional[str] = Body(None, embed=True, description="클릭한 사용자 ID"),
    session_id: Optional[str] = Body(None, embed=True, description="세션 ID (비로그인 사용자)")
):
    """
    광고 클릭 이벤트를 수신하여 로깅 서비스로 전달(위임)합니다.
    실제 로그 저장은 로깅 서비스가 담당합니다.
    이 API는 요청을 받고 빠르게 응답하는 것을 목표로 할 수 있습니다 (Accepted).
    """
    # 광고 존재 여부 확인 (선택적이지만, 유효한 광고 클릭인지 확인 가능)
    ad_doc = await crud.get_advertisement_by_id(ad_id)
    if not ad_doc:
        # 존재하지 않는 광고에 대한 클릭 시도를 로깅할지, 아니면 에러 처리할지 정책 필요
        # 여기서는 로깅 시도 없이 404 반환
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="클릭 대상 광고를 찾을 수 없습니다.")

    log_data = AdClickLogData(
        advertisement_id=ad_id, # MongoDB ID를 그대로 사용
        user_id=user_id,
        session_id=session_id
    )

    log_sent_successfully = await services.send_ad_click_log(log_data)

    if log_sent_successfully:
        return {"message": "광고 클릭 로그가 로깅 서비스로 전달 요청되었습니다."}
    else:
        # 로깅 서비스 호출 실패 시, 어떻게 처리할지?
        # 503 Service Unavailable 또는 다른 에러 코드 반환 고려
        # 또는, 내부적으로 재시도 로직을 두거나, 실패 로그를 별도로 기록할 수도 있음
        # 여기서는 간단히 실패 메시지 반환 (하지만 상태 코드는 여전히 202일 수 있음)
        logger.error(f"Failed to delegate ad click log for ad_id: {ad_id} to logging service.")
        # 주 서비스 흐름에 영향을 주지 않으려면, 에러를 발생시키지 않고 성공처럼 응답할 수도 있음.
        # raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="로깅 서비스 호출에 실패했습니다.")
        return {"message": "광고 클릭 로그 전달 요청 중 문제가 발생했습니다. (로깅 서비스 확인 필요)"}


# --- 이하 광고 관리용 CRUD API (관리자 권한 필요 - 여기서는 인증/권한 로직 생략) ---

@app.post("/advertisements/", response_model=AdvertisementResponse, status_code=status.HTTP_201_CREATED, summary="새 광고 생성 (관리자용)")
async def create_new_advertisement(ad: AdvertisementCreate):
    created_ad_doc = await crud.create_advertisement(ad)
    if not created_ad_doc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="광고 생성에 실패했습니다.")
    return AdvertisementResponse.model_validate(created_ad_doc)

@app.get("/advertisements/{ad_id}", response_model=AdvertisementResponse, summary="특정 광고 정보 조회 (관리자용)")
async def read_advertisement(ad_id: str = Path(..., description="광고의 MongoDB ID")):
    ad_doc = await crud.get_advertisement_by_id(ad_id)
    if not ad_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="광고를 찾을 수 없습니다.")
    return AdvertisementResponse.model_validate(ad_doc)

@app.put("/advertisements/{ad_id}", response_model=AdvertisementResponse, summary="광고 정보 수정 (관리자용)")
async def update_existing_advertisement(
    ad_data: AdvertisementUpdate,
    ad_id: str = Path(..., description="수정할 광고의 MongoDB ID")
):
    updated_ad_doc = await crud.update_advertisement(ad_id, ad_data)
    if not updated_ad_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="광고를 찾을 수 없거나 업데이트에 실패했습니다.")
    return AdvertisementResponse.model_validate(updated_ad_doc)

@app.delete("/advertisements/{ad_id}", status_code=status.HTTP_204_NO_CONTENT, summary="광고 삭제 (관리자용)")
async def remove_advertisement(ad_id: str = Path(..., description="삭제할 광고의 MongoDB ID")):
    deleted = await crud.delete_advertisement(ad_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="삭제할 광고를 찾을 수 없습니다.")
    return # No content