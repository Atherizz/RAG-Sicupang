from app.db.database import DBService

_db_service = None

def get_db_service():
    """Get singleton instance of DBService with lazy initialization"""
    global _db_service
    if _db_service is None:
        _db_service = DBService()
    return _db_service

# Export untuk kemudahan import
__all__ = ['DBService', 'get_db_service']