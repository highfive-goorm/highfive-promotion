from typing import List

import requests
from fastapi import APIRouter, HTTPException, FastAPI
from datetime import datetime

from database import order_collection
from schemas import OrderCreate, OrderInDB

app = FastAPI()
router = APIRouter(prefix="/order", tags=["Order"])

app.include_router(router)


def serialize_order(order) -> dict:
    del order["id"]
    return order


@router.post("/{is_from_cart}", response_model=OrderInDB)
async def create_order(order: OrderCreate, is_from_cart: bool):
    now = datetime.utcnow()
    doc = order.dict()
    doc["created_at"] = now
    doc["updated_at"] = now
    result = await order_collection.insert_one(doc)
    doc["id"] = result.inserted_id

    if is_from_cart:
        # 카트에서 주문한 경우: 주문 완료 후 카트 비우기
        try:
            requests.delete(f'http://cart:8000/{order.user_id}')
        except requests.RequestException as e:
            print(f"카트 삭제 실패: {e}")
        return serialize_order(doc)
    else:
        # 일반 주문 (장바구니 아님)
        return serialize_order(doc)



@router.get("/{user_id}", response_model=List[OrderInDB])
async def get_orders_by_user(user_id: int):
    cursor = order_collection.find({"user_id": user_id})
    orders = []
    async for doc in cursor:
        orders.append(serialize_order(doc))

    if not orders:
        raise HTTPException(status_code=404, detail="No orders found for this user")

    return orders


@router.get("/{id}", response_model=OrderInDB)
async def get_order(id: int):
    order = await order_collection.find_one({"id": id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return serialize_order(order)


@router.put("/{id}", response_model=OrderInDB)
async def update_order(id: int, order: OrderCreate):
    doc = order.dict()
    doc["updated_at"] = datetime.utcnow()
    result = await order_collection.update_one(
        {"id": id},
        {"$set": doc}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    updated = await order_collection.find_one({"id": id})
    return serialize_order(updated)


@router.delete("/{id}")
async def delete_order(id: int):
    result = await order_collection.delete_one({"id": id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order deleted"}
