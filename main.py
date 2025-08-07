from fastapi import FastAPI
from app.routes import food_recommendation

app = FastAPI(title="Emolog API")

app.include_router(food_recommendation.router, prefix="/api")
