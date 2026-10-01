from datetime import datetime, timezone
from decimal import Decimal
from .purchase_return_repository import PurchaseReturnRepository
from .purchase_repositories import PurchaseRepository
from .services import StockMovementService


class PurchaseReturnService:
    def __init__(self):
        self.repository=PurchaseReturnRepository(); self.purchase_repository=PurchaseRepository(); self.stock=StockMovementService()

    def create_return(self, return_number, purchase_id, items, reason="", created_by=None):
        if not return_number: raise ValueError("returnNumber wajib diisi.")
        if self.repository.find_by_number(return_number): raise ValueError("returnNumber sudah digunakan.")
        purchase=self.purchase_repository.find_by_id(purchase_id)
        if not purchase: raise ValueError("Pembelian tidak ditemukan.")
        if not isinstance(items,list) or not items: raise ValueError("Minimal satu item retur harus dipilih.")
        purchase_map={str(i.get("productId")):i for i in purchase.get("items",[])}
        previous={}
        for ret in self.repository.find_by_purchase(purchase_id):
            for i in ret.get("items",[]): previous[str(i.get("productId"))]=previous.get(str(i.get("productId")),0)+int(i.get("quantity",0))
        processed=[]; total=Decimal("0")
        for item in items:
            pid=str(item.get("productId")); qty=int(item.get("quantity",0))
            if pid not in purchase_map: raise ValueError(f"Produk {pid} tidak ada dalam pembelian.")
            if qty<=0: raise ValueError("Quantity retur harus lebih besar dari 0.")
            max_qty=int(purchase_map[pid].get("quantity",0))-previous.get(pid,0)
            if qty>max_qty: raise ValueError(f"Quantity retur melebihi sisa pembelian ({max_qty}).")
            price=Decimal(str(purchase_map[pid].get("purchasePrice",0))); subtotal=price*qty; total+=subtotal
            processed.append({"productId":pid,"quantity":qty,"purchasePrice":float(price),"subtotal":float(subtotal)})
        now=datetime.now(timezone.utc)
        data={"returnNumber":return_number,"purchaseId":purchase_id,"supplierId":purchase.get("supplierId"),"returnDate":now,"items":processed,"reason":reason,"amount":float(total),"status":"PENDING","createdBy":created_by,"createdAt":now,"updatedAt":now}
        return self.repository.create(data)

    def approve(self, return_id, approved_by=None):
        ret=self.repository.claim_for_approval(return_id)
        if not ret: raise ValueError("Retur pembelian tidak ditemukan atau sedang/telah diproses.")
        movements=[]
        try:
            for item in ret.get("items",[]):
                movements.append(self.stock.create_movement(product_id=item["productId"],movement_type="OUT",quantity=int(item["quantity"]),reference_type="PURCHASE_RETURN",reference_id=str(ret["_id"]),notes=f"Retur pembelian {ret['returnNumber']}",created_by=approved_by))
        except Exception:
            for m in reversed(movements): self.stock.repository.rollback_movement(m)
            self.repository.update(return_id,{"status":"PENDING"})
            raise
        updated = self.repository.update(return_id,{"status":"APPROVED","approvedBy":approved_by,"approvedAt":datetime.now(timezone.utc)})
        if getattr(updated, "modified_count", 0) != 1:
            for m in reversed(movements):
                try:
                    self.stock.repository.rollback_movement(m)
                except Exception:
                    pass
            self.repository.update(return_id,{"status":"PENDING"})
            raise RuntimeError("Status retur pembelian gagal diperbarui menjadi APPROVED.")
        return updated
