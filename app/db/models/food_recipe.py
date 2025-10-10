from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, select, Session
from sqlalchemy import Column, String, Index
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

class FoodRecipe(SQLModel, table=True):
    __tablename__ = "resep_makanan"

    id_resep_makanan: Optional[int] = Field(default=None, primary_key=True)
    nama_olahan: str = Field(index=True, unique=True)
    id_resep_vektor_db: str = Field(sa_column_kwargs={"nullable": False},  index=True)
    uraian_bahan: dict = Field(sa_column=Column(JSON)) 
    standar_porsi: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


def get_resep_by_nama(nama_olahan: str, session: Session) -> Optional[FoodRecipe]:
    statement = select(FoodRecipe).where(FoodRecipe.nama_olahan == nama_olahan)
    return session.exec(statement).first()


def get_resep_by_vec_id(vec_id: str, session: Session) -> Optional[FoodRecipe]:
    statement = select(FoodRecipe).where(FoodRecipe.id_resep_vektor_db == vec_id)
    return session.exec(statement).first()

def InsertFoodRecipe(foodRecipe: FoodRecipe, session: Session) -> FoodRecipe:
    session.add(foodRecipe)
    session.commit()
    session.refresh(foodRecipe)
    return foodRecipe
