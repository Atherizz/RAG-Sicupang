from pydantic import BaseModel
from typing import List

class FoodInput(BaseModel):
    food_name: str
    portion: int
    
class FoodBatchRequest(BaseModel):
    family_id : int
    items: List[FoodInput]
    
class FoodExtract(BaseModel):
    food_name: List[str]
    
