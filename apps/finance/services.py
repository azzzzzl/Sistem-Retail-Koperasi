from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from .repository import ExpenseRepository


def _normalize_datetime(value):
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return value


class ExpenseService:
    CATEGORIES={"Listrik","Air","Transportasi","ATK","Perawatan","Operasional lainnya"}
    PAYMENT_METHODS={"CASH","TRANSFER","QRIS","OTHER"}
    def __init__(self, repository=None): self.repository=repository or ExpenseRepository()
    def create(self, expense_number, date=None, category="Operasional lainnya", description="", amount=0, payment_method="CASH", reference_number="", created_by=None):
        if not expense_number: raise ValueError("Nomor pengeluaran wajib diisi.")
        if self.repository.exists_number(expense_number): raise ValueError("Nomor pengeluaran sudah digunakan.")
        try: amount=Decimal(str(amount))
        except (InvalidOperation,TypeError,ValueError) as exc: raise ValueError("Jumlah pengeluaran harus berupa angka.") from exc
        if amount<=0: raise ValueError("Jumlah pengeluaran harus lebih besar dari 0.")
        if category not in self.CATEGORIES: raise ValueError("Kategori pengeluaran tidak valid.")
        payment_method=payment_method.upper()
        if payment_method not in self.PAYMENT_METHODS: raise ValueError("Metode pembayaran tidak valid.")
        now=datetime.now(timezone.utc)
        if date is None: date=now
        date = _normalize_datetime(date)
        data={"expenseNumber":expense_number,"date":date,"category":category,"description":description,"amount":float(amount),"paymentMethod":payment_method,"referenceNumber":reference_number or None,"createdBy":created_by,"createdAt":now,"updatedAt":now}
        return self.repository.create(data)
    def list(self): return self.repository.find_all()
    def get(self,item_id): return self.repository.find_by_id(item_id)
    def update(self, item_id, data):
        updates = dict(data)
        if "amount" in updates:
            try: amount = Decimal(str(updates["amount"]))
            except (InvalidOperation, TypeError, ValueError) as exc: raise ValueError("Jumlah pengeluaran harus berupa angka.") from exc
            if amount <= 0: raise ValueError("Jumlah pengeluaran harus lebih besar dari 0.")
            updates["amount"] = float(amount)
        if "category" in updates and updates["category"] not in self.CATEGORIES:
            raise ValueError("Kategori pengeluaran tidak valid.")
        if "paymentMethod" in updates:
            method = str(updates["paymentMethod"]).upper()
            if method not in self.PAYMENT_METHODS: raise ValueError("Metode pembayaran tidak valid.")
            updates["paymentMethod"] = method
        return self.repository.update(item_id, updates)
