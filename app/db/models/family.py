from typing import Optional
from datetime import date
from decimal import Decimal
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Enum as SQLEnum
from sqlalchemy.types import Numeric, Date

# class Konfirmasi(str, SQLEnum):
#     Ya = "Ya"
#     Tidak = "Tidak"
    
# class StatusKeluarga(str, SQLEnum):
#     MENUNGGU = "MENUNGGU"
#     DITERIMA = "DITERIMA"
#     DITOLAK = "DITOLAK"

# # Ambil list nilai string dari Enum yang sudah didefinisikan
# KONFIRMASI_VALUES = [member.value for member in Konfirmasi]
# STATUS_KELUARGA_VALUES = [member.value for member in StatusKeluarga]


class Family(SQLModel, table=True):
    __tablename__ = "keluarga"

    id_keluarga: Optional[int] = Field(default=None, primary_key=True)
    nomor_kartu_keluarga: Optional[str] = Field(default=None, max_length=16, sa_column_kwargs={"index": True})
    nama_kepala_keluarga: str = Field(max_length=255)
    jumlah_keluarga: int
    alamat: str = Field(max_length=255)
    gambar: str = Field(max_length=255)
    

    komentar: Optional[str] = Field(default=None, max_length=200)
    id_pengguna: int = Field(foreign_key="pengguna.id_pengguna")
    id_kecamatan: int = Field(foreign_key="kecamatan.id_kecamatan", index=True)
    id_desa: int = Field(foreign_key="desa.id_desa", index=True)

    rentang_pendapatan: int = Field(foreign_key="rentang_uang.id_rentang_uang", index=True)
    rentang_pengeluaran: int = Field(foreign_key="rentang_uang.id_rentang_uang", index=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
