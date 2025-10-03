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
async def ingredient_extract(request: FoodExtract, session: Session = Depends(db.get_session)):
    svc = IngredientExtract()
    results = await svc.build_augmented_message(request.food_name, session=session) 
    return {"response": results}