from typing import Optional, List, Tuple
from decimal import Decimal
from sqlmodel import SQLModel, Field, Session, select
from sqlalchemy import Column, String, Index
from sqlalchemy.types import Numeric
from fuzzywuzzy import fuzz
from fuzzywuzzy import process 


# VARIABEL GLOBAL CACHE: Diinisialisasi None, akan diisi saat pertama kali diakses.
_CACHED_PANGAN_NAMES: Optional[List[str]] = None


class FoodIngredient(SQLModel, table=True):
    __tablename__ = "pangan"
    __table_args__ = (
        Index("id_jenis_pangan", "id_jenis_pangan"),
        Index("id_takaran", "id_takaran"),
        {"extend_existing": True},
    )

    id_pangan: Optional[int] = Field(default=None, primary_key=True)

    nama_pangan: str = Field(
        sa_column=Column(String(191), nullable=False)
    )

    gram: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    kalori: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    lemak: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    karbohidrat: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    protein: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))

    id_jenis_pangan: int = Field(foreign_key="jenis_pangan.id_jenis_pangan")
    id_takaran: int = Field(foreign_key="takaran.id_takaran")

    referensi_urt: str = Field(
        sa_column=Column(String(255), nullable=False)
    )
    referensi_gram_berat: Decimal = Field(
        sa_column=Column(Numeric(10, 2), nullable=False)
    )
    
FUZZY_SCORE_THRESHOLD = 70


def _load_pangan_names(session: Session) -> List[str]:
    """
    Mengambil semua nama pangan dari database dan menyimpannya di cache global.
    Hanya berjalan saat _CACHED_PANGAN_NAMES masih None.
    """
    global _CACHED_PANGAN_NAMES
    
    if _CACHED_PANGAN_NAMES is not None:
        return _CACHED_PANGAN_NAMES
    
    print("⏳ [CACHE MISS] Loading all Pangan names from DB...")
    statement_names = select(FoodIngredient.nama_pangan)
    all_pangan_names: List[str] = session.exec(statement_names).all()
    
    _CACHED_PANGAN_NAMES = all_pangan_names
    return all_pangan_names


def get_pangan_by_nama_fuzzy(nama_pangan: str, session: Session) -> Optional[FoodIngredient]:
    """
    Mencari FoodIngredient yang nama pangannya paling mirip menggunakan fuzzy matching.
    Menggunakan cache global untuk daftar nama pangan (all_pangan_names).
    """
    
    all_pangan_names = _load_pangan_names(session)

    if not all_pangan_names:
        return None

    best_match: Optional[Tuple[str, int]] = process.extractOne(
        nama_pangan, 
        all_pangan_names, 
        scorer=fuzz.ratio
    )

    if best_match is None:
        return None

    best_name, score = best_match

    if score >= FUZZY_SCORE_THRESHOLD:
        statement = select(FoodIngredient).where(FoodIngredient.nama_pangan == best_name)
        return session.exec(statement).first()
    else:
        return None


def get_pangan_by_nama_like(nama_pangan: str, session: Session) -> Optional[List['FoodIngredient']]:
    search_pattern = f"%{nama_pangan}%"

    statement = select(FoodIngredient).where(FoodIngredient.nama_pangan.ilike(search_pattern))
    
    results: List['FoodIngredient'] = session.exec(statement).all()
    
    if results:
        return results
    else:
        return None


def InsertPangan(pangan: FoodIngredient, session: Session) -> FoodIngredient:
    session.add(pangan)
    session.commit()
    session.refresh(pangan)
    return pangan