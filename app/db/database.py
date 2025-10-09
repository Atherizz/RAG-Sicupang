from sqlmodel import create_engine, Session, SQLModel
from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class DBService:
    def __init__(self):
        # Validasi environment variables
        self.DB_USER = os.getenv("DB_USER")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD")
        self.DB_NAME = os.getenv("DB_NAME")
        
        if not all([self.DB_USER, self.DB_PASSWORD, self.DB_NAME]):
            raise ValueError(
                "DB_USER, DB_PASSWORD, and DB_NAME must be set in environment variables"
            )
        
        # Mengambil NAMA KONEKSI untuk Cloud Run
        self.INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")
        
        # Setup connection string
        if self.INSTANCE_CONNECTION_NAME:
            # Production: Cloud Run + Cloud SQL (Unix Socket)
            self.mysql_url = (
                f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
                f"@/{self.DB_NAME}?unix_socket=/cloudsql/{self.INSTANCE_CONNECTION_NAME}"
            )
            logger.info(f"Using Cloud SQL connection: {self.INSTANCE_CONNECTION_NAME}")
        else:
            # Local development: TCP connection
            self.DB_HOST = os.getenv("DB_HOST", "localhost")
            self.DB_PORT = os.getenv("DB_PORT", "3306")
            self.mysql_url = (
                f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
            logger.info(f"Using local MySQL connection: {self.DB_HOST}:{self.DB_PORT}")
    
        self.engine = create_engine(
            self.mysql_url,
            echo=False,
            pool_size=5,            
            max_overflow=10,     
            pool_pre_ping=True,    
            pool_recycle=3600  
        )
        
        logger.info("Database engine initialized successfully")
    
    def get_sql_database(self):
        """Get LangChain SQLDatabase instance"""
        return SQLDatabase.from_uri(self.mysql_url)
    
    def get_session(self):
        """Get SQLModel session (generator for dependency injection)"""
        with Session(self.engine) as session:
            yield session
    
    def create_db_and_tables(self):
        """Create all tables defined in SQLModel models"""
        SQLModel.metadata.create_all(self.engine)
        logger.info("Database tables created successfully")