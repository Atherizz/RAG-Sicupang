from sqlmodel import create_engine, Session, SQLModel
from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv
import os

load_dotenv()

class DBService:
    def __init__(self):
        # Gunakan DATABASE_URL langsung dari environment
        self.database_url = os.getenv("DATABASE_URL")
        
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        
        # Pastikan menggunakan driver yang benar untuk PostgreSQL
        # Ganti 'postgres://' dengan 'postgresql://' jika perlu (untuk compatibility)
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)
        
        self.engine = create_engine(self.database_url, echo=False)
        
    def get_sql_database(self):
        db = SQLDatabase.from_uri(self.database_url)
        return db
    
    def get_session(self):
        with Session(self.engine) as session:
            yield session
            
    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)
        