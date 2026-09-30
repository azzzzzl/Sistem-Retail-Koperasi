from datetime import datetime, timezone

from database.mongodb import db


class SupplierInvoiceRepository:
    COLLECTION_NAME = "supplier_invoices"

    def __init__(self):
        self.collection = db[self.COLLECTION_NAME]

    def create(self, invoice_data):
        result = self.collection.insert_one(invoice_data)

        return self.collection.find_one(
            {"_id": result.inserted_id}
        )

    def find_all(self):
        return list(
            self.collection.find().sort(
                "createdAt",
                -1,
            )
        )

    def find_by_id(self, invoice_id):
        from bson import ObjectId

        try:
            object_id = ObjectId(invoice_id)
        except Exception:
            return None

        return self.collection.find_one(
            {"_id": object_id}
        )

    def find_by_number(self, invoice_number):
        return self.collection.find_one(
            {
                "invoiceNumber": invoice_number
            }
        )

    def find_by_supplier_id(self, supplier_id):
        return list(
            self.collection.find(
                {
                    "supplierId": supplier_id
                }
            ).sort(
                "dueDate",
                1,
            )
        )

    def find_by_purchase_id(self, purchase_id):
        return list(
            self.collection.find(
                {
                    "purchaseId": purchase_id
                }
            ).sort(
                "createdAt",
                -1,
            )
        )

    def find_by_status(self, status):
        return list(
            self.collection.find(
                {
                    "status": status
                }
            ).sort(
                "dueDate",
                1,
            )
        )

    def update(self, invoice_id, update_data):
        from bson import ObjectId

        try:
            object_id = ObjectId(invoice_id)
        except Exception:
            return None

        update_data["updatedAt"] = datetime.now(
            timezone.utc
        )

        self.collection.update_one(
            {"_id": object_id},
            {"$set": update_data},
        )

        return self.collection.find_one(
            {"_id": object_id}
        )
