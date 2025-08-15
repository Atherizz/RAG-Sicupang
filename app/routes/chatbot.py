from fastapi import APIRouter
from app.services.feature.chatbot import Chatbot
from pydantic import BaseModel

router = APIRouter()
chatbot = Chatbot()

class ChatbotInput(BaseModel):
    prompt: str
    
@router.post("/sicupang-ai")
def get_recommendation(input: ChatbotInput):
    result = chatbot.ask(input.prompt)
    return {"response": result}

