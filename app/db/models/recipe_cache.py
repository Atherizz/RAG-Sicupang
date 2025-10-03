from sqlmodel import SQLModel, Field, select, Session
from typing import Optional, List
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON

from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


from sqlalchemy import Column
from sqlalchemy.types import JSON

class RecipeCache(SQLModel, table=True):
    __tablename__ = "resep_cache"
    
    id_resep_cache: Optional[int] = Field(default=None, primary_key=True)
    nama_olahan: str = Field(index=True, unique=True)
    resep_id_vdb: str = Field(sa_column_kwargs={"nullable": False})


    bahan_parsed: dict = Field(sa_column=Column(JSON)) 
    
    standar_porsi: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
def GetRecipeCacheByName(nama_olahan: str, session: Session) -> Optional[RecipeCache]:
    """Mengambil satu objek RecipeCache berdasarkan nama_olahan yang unik."""
    
    statement = select(RecipeCache).where(RecipeCache.nama_olahan == nama_olahan)
    
    result = session.exec(statement).first()

    return result

