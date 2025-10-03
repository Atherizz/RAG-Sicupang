from fastapi import FastAPI
from app.routes import food_recommendation, chatbot, ingredient_extract

app = FastAPI(title="Emolog API")

app.include_router(food_recommendation.router, prefix="/api")
app.include_router(chatbot.router, prefix="/api")
app.include_router(ingredient_extract.router, prefix="/api")