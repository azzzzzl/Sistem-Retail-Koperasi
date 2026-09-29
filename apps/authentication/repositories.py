from datetime import datetime, timezone

from bson import ObjectId

from database.mongodb import get_database


class UserRepository:
    def __init__(self):
        self.db = get_database()
        self.collection = self.db["users"]

    def create_indexes(self):
        self.collection.create_index("username", unique=True)

    def create(self, user_data):
        return self.collection.insert_one(user_data)

    def find_by_username(self, username):
        return self.collection.find_one({"username": username})

    def find_by_id(self, user_id):
        try:
            object_id = ObjectId(user_id)
        except Exception:
            return None

        return self.collection.find_one({"_id": object_id})

    def find_all(self):
        return list(self.collection.find())

    def update_password(self, user_id, password_hash):
        try:
            object_id = ObjectId(user_id)
        except Exception:
            return None

        return self.collection.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "passwordHash": password_hash,
                    "updatedAt": datetime.now(timezone.utc),
                }
            }
        )

    def update(self, user_id, update_data):
        try:
            object_id = ObjectId(user_id)
        except Exception:
            return None

        update_data["updatedAt"] = datetime.now(timezone.utc)

        return self.collection.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )

    def update_status(self, user_id, status):
        try:
            object_id = ObjectId(user_id)
        except Exception:
            return None

        return self.collection.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "status": status,
                    "updatedAt": datetime.now(timezone.utc),
                }
            }
        )

    def update_role(self, user_id, role):
        try:
            object_id = ObjectId(user_id)
        except Exception:
            return None

        return self.collection.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "role": role,
                    "updatedAt": datetime.now(timezone.utc),
                }
            }
        )