from database.mongodb import get_database


class PaymentRepository:
    def __init__(self):
        self.db = get_database()
        self.payments = self.db["payments"]

    def create_payment(self, payment_data):
        result = self.payments.insert_one(payment_data)
        return result.inserted_id

    def get_payment(self, payment_id):
        return self.payments.find_one({"_id": payment_id})

    def get_payments(self, limit=50):
        return list(self.payments.find().sort("paidAt", -1).limit(limit))

    def delete_payment(self, payment_id):
        return self.payments.delete_one({"_id": payment_id})

    def get_payments_by_sale(self, sale_id):
        return list(self.payments.find({"saleId": sale_id}).sort("paidAt", -1))


    def mark_sale_refunded(self, sale_id, refunded_by=None):
        from datetime import datetime, timezone
        return self.payments.update_many(
            {"saleId": sale_id},
            {"$set": {"status": "REFUNDED", "refundedBy": refunded_by, "refundedAt": datetime.now(timezone.utc)}},
        )


    def create_refund(self, sale_id, return_id, amount, refunded_by=None):
        from datetime import datetime, timezone
        data = {
            "saleId": sale_id,
            "returnId": return_id,
            "type": "REFUND",
            "paymentMethod": "REFUND",
            "amount": float(amount),
            "paidAt": datetime.now(timezone.utc),
            "refundedBy": refunded_by,
            "status": "REFUNDED",
        }
        result = self.payments.insert_one(data)
        return self.payments.find_one({"_id": result.inserted_id})

    def delete_refund(self, refund_id):
        return self.delete_payment(refund_id)
