from database.mongodb import get_database
from datetime import datetime, timezone


class AuditLogRepository:
    def __init__(self):
        self.collection = get_database()["audit_logs"]

    def create(self, data):
        result = self.collection.insert_one(data)
        return self.collection.find_one({"_id": result.inserted_id})

    def find_all(self, query=None, limit=200):
        return list(
            self.collection.find(query or {})
            .sort("createdAt", -1)
            .limit(limit)
        )
