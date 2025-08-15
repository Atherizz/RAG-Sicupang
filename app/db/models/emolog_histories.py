from sqlmodel import SQLModel,Field,select
from typing import Optional
from datetime import datetime
from sqlmodel import Session
from fastapi import HTTPException
from typing import List

class EmologHistories(SQLModel, table=True):
    __tablename__ = "emolog_histories"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)  
    subdistrict_id: int = Field(index=True) 
    emotion_label: str = Field(index=True)
    text_input: str = Field(index=True)
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
def InsertHistory(history: EmologHistories, session: Session) -> EmologHistories:
    session.add(history)
    session.commit()
    session.refresh(history)
    return history

def GetHistoryByUserId(user_id: int, session: Session) -> List[EmologHistories]:
    statement = select(EmologHistories).where(EmologHistories.user_id == user_id)
    results = session.exec(statement).all()
    if not results:
        return "anda belum pernah menulis diary emolog!"
    return results