from fastapi import FastAPI, HTTPException
from typing import List

from .crud import (
    create_promotion,
    get_active_promotions,
    get_promotion,
    update_promotion,
    delete_promotion,
)
from .schemas import PromotionCreate, PromotionUpdate, PromotionInDB

app = FastAPI(title="프로모션 서비스 API")

@app.post("/promotion", response_model=PromotionInDB, status_code=201, tags=["Promotions"])
async def handle_create_promotion(promotion: PromotionCreate):
    created_promotion = await create_promotion(promotion)
    return created_promotion

@app.get("/promotion/active", response_model=List[PromotionInDB], tags=["Promotions"])
async def handle_read_active_promotions(skip: int = 0, limit: int = 10):

    promotions = await get_active_promotions(skip, limit)
    return promotions

@app.get("/promotion/{promotion_id}", response_model=PromotionInDB, tags=["Promotions"])
async def handle_read_promotion(promotion_id: str):
    promotion = await get_promotion(promotion_id)
    if promotion is None:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return promotion

@app.patch("/promotion/{promotion_id}", response_model=PromotionInDB, tags=["Promotions"])
async def handle_update_promotion(promotion_id: str, promotion_update: PromotionUpdate):
    updated_promotion = await update_promotion(promotion_id, promotion_update)
    if updated_promotion is None:
        raise HTTPException(status_code=404, detail="Promotion not found to update")
    return updated_promotion

@app.delete("/promotion/{promotion_id}", status_code=204, tags=["Promotions"])
async def handle_delete_promotion(promotion_id: str):
    success = await delete_promotion(promotion_id)
    if not success:
        raise HTTPException(status_code=404, detail="Promotion not found to delete")
    return None # 성공 시 204 No Content는 본문이 없어야 함

@app.get("/health", status_code=200, tags=["Health Check"])
async def health_check():
    return {"status": "ok"}
