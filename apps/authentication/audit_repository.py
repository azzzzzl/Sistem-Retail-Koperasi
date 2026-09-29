from datetime import datetime, timezone

from database.mongodb import get_database


class AuditLogRepository:
    def __init__(self):
        self.db = get_database()
        self.collection = self.db["audit_logs"]

        self.collection.create_index(
            "createdAt"
        )
        self.collection.create_index(
            "username"
        )
        self.collection.create_index(
            "action"
        )

    def create(self, log_data):
        return self.collection.insert_one(log_data)

    def find_all(self):
        return list(
            self.collection.find().sort(
                "createdAt",
                -1
            )
        )