from datetime import datetime, timezone

from database.mongodb import db


class SupplierPaymentRepository:
    COLLECTION_NAME = "supplier_payments"

    def __init__(self):
        self.collection = db[self.COLLECTION_NAME]

    def create(self, payment_data):
        result = self.collection.insert_one(payment_data)
        return self.collection.find_one({"_id": result.inserted_id})

    def find_all(self):
        return list(
            self.collection.find().sort("createdAt", -1)
        )

    def find_by_id(self, payment_id):
        from bson import ObjectId

        try:
            object_id = ObjectId(payment_id)
        except Exception:
            return None

        return self.collection.find_one({"_id": object_id})

    def find_by_number(self, payment_number):
        return self.collection.find_one(
            {"paymentNumber": payment_number}
        )

    def find_by_invoice_id(self, invoice_id):
        return list(
            self.collection.find({"invoiceId": invoice_id})
            .sort("createdAt", -1)
        )

    def find_by_supplier_id(self, supplier_id):
        return list(
            self.collection.find({"supplierId": supplier_id})
            .sort("createdAt", -1)
        )

    def update(self, payment_id, update_data):
        from bson import ObjectId

        try:
            object_id = ObjectId(payment_id)
        except Exception:
            return None

        update_data["updatedAt"] = datetime.now(timezone.utc)

        self.collection.update_one(
            {"_id": object_id},
            {"$set": update_data},
        )

        return self.collection.find_one({"_id": object_id})

    def delete(self, payment_id):
        from bson import ObjectId
        try:
            object_id = ObjectId(payment_id)
        except Exception:
            return None
        return self.collection.delete_one({"_id": object_id})
