from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class ChatbotHistory(SQLModel, table=True):
    __tablename__ = "chatbot_histories"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    session_id: str
    message: str
    sender: str 
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    
    