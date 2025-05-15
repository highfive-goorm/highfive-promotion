from fastapi import FastAPI, HTTPException, status, Depends
from typing import List
from .schemas import PromotionInDB, PromotionCreate, PromotionUpdate
from .crud import (
    create_promotion, get_promotion, list_promotions,
    update_promotion, delete_promotion
)

app = FastAPI()

@app.post("/promotion", response_model=PromotionInDB, status_code=201)
async def create(promotion: PromotionCreate):
    doc = await create_promotion(promotion)
    return PromotionInDB(**doc)

@app.get("/promotion", response_model=List[PromotionInDB])
async def list_all():
    docs = await list_promotions()
    return [PromotionInDB(**doc) for doc in docs]

@app.get("/promotion/{id}", response_model=PromotionInDB)
async def get(id: int):
    doc = await get_promotion(id)
    if not doc:
        raise HTTPException(404, "Promotion not found")
    return PromotionInDB(**doc)

@app.put("/promotion/{id}", response_model=PromotionInDB)
async def update(id: int, update: PromotionUpdate):
    doc = await update_promotion(id, update)
    if not doc:
        raise HTTPException(404, "Promotion not found")
    return PromotionInDB(**doc)

@app.delete("/promotion/{id}", status_code=204)
async def delete(id: int):
    deleted = await delete_promotion(id)
    if not deleted:
        raise HTTPException(404, "Promotion not found")
    return
