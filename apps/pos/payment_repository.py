from database.mongodb import get_database


class PaymentRepository:
    def __init__(self):
        self.db = get_database()
        self.payments = self.db["payments"]

    def create_payment(self, payment_data):
        result = self.payments.insert_one(payment_data)
        return result.inserted_id

    def get_payment(self, payment_id):
        return self.payments.find_one({
            "_id": payment_id
        })

    def get_payments(self, limit=50):
        return list(
            self.payments.find()
            .sort("paidAt", -1)
            .limit(limit)
        )