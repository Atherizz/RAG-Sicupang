# app/db/database.py
from sqlmodel import SQLModel, Session, create_engine
from dotenv import load_dotenv
import os

load_dotenv()

class DBService:
    def __init__(self) -> None:
        url = os.getenv("DATABASE_URL")
        if not url:
            raise RuntimeError("DATABASE_URL tidak ditemukan di environment")

        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)

        self.engine = create_engine(
            url,
            echo=False,
            pool_pre_ping=True,   # auto test koneksi (hindari 'server closed the connection')
            pool_recycle=3600,    # recycle tiap 1 jam (aman untuk provider managed)
            # connect_args={}      # biasanya tidak perlu; sslmode di URL sudah cukup
        )

    def get_session(self):
        """Dipakai di FastAPI: Depends(db.get_session)"""
        with Session(self.engine) as session:
            yield session

