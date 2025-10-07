from typing import Optional
from datetime import date
from decimal import Decimal
from sqlmodel import SQLModel, Field, Session
from sqlalchemy import Column
from sqlalchemy.types import Numeric, Date

from .family import Family 

class HouseholdFood(SQLModel, table=True):
    __tablename__ = "pangan_keluarga"
    __table_args__ = {"extend_existing": True}  

    id_pangan_keluarga: Optional[int] = Field(default=None, primary_key=True)
    id_pangan: int = Field(foreign_key="pangan.id_pangan")
    id_keluarga: int = Field(foreign_key="keluarga.id_keluarga")

    urt: Decimal = Field(sa_column=Column(Numeric(8, 2), nullable=False))
    tanggal: date = Field(sa_column=Column(Date, nullable=False))

def InsertHouseholdFood(houseHoldFood: HouseholdFood, session: Session) -> HouseholdFood:
    session.add(houseHoldFood)
    session.commit()
    session.refresh(houseHoldFood)
    return houseHoldFood