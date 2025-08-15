from sqlmodel import SQLModel,Field
from typing import Optional
from datetime import datetime
from sqlmodel import Session
from fastapi import HTTPException

class User(SQLModel, table=True):
    __tablename__ = "users" 
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
    password: str
    role: str
    nip: Optional[str] = Field(default=None)
    str_proof: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
def GetUserById(user_id: int , session: Session) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user