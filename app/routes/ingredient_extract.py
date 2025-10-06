from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.schemas.request_model import FoodBatchRequest, FoodExtract
from app.db.database import DBService
from app.services.feature.ingredient_extract import IngredientExtract
from pydantic import BaseModel
from typing import List

router = APIRouter()
db = DBService()

    
@router.post("/ingredient-extract")
async def ingredient_extract(request: FoodBatchRequest, session: Session = Depends(db.get_session)):
    svc = IngredientExtract()
    results = await svc.searchingFood(request.items, request.family_id, session)
    return {"response": results}

@router.post("/ai-extract")
async def ai_extract(request: FoodExtract, session: Session = Depends(db.get_session)):
    svc = IngredientExtract()
    results = await svc.build_augmented_message_bulk(request.food_name, session)
    return {"response": results}