from datetime import datetime, timezone

from .opname_repositories import StockOpnameRepository
from .services import StockMovementService


class StockOpnameService:
    """
    Service untuk business logic Stock Opname.
    """

    STATUS_DRAFT = "DRAFT"
    STATUS_SUBMITTED = "SUBMITTED"
    STATUS_APPROVED = "APPROVED"

    ALLOWED_STATUSES = {
        STATUS_DRAFT,
        STATUS_SUBMITTED,
        STATUS_APPROVED,
    }

    def __init__(self):
        self.repository = StockOpnameRepository()
        self.stock_movement_service = StockMovementService()

    def create_opname(
        self,
        opname_number,
        items,
        created_by=None,
    ):
        if not opname_number:
            raise ValueError(
                "opnameNumber wajib diisi."
            )

        if not isinstance(items, list) or not items:
            raise ValueError(
                "Items opname wajib diisi."
            )

        existing_opname = (
            self.repository.find_by_number(
                opname_number
            )
        )

        if existing_opname:
            raise ValueError(
                "opnameNumber sudah digunakan."
            )

        processed_items = []

        for item in items:
            product_id = item.get("productId")

            if not product_id:
                raise ValueError(
                    "productId wajib diisi."
                )

            physical_stock = item.get(
                "physicalStock"
            )

            try:
                physical_stock = int(
                    physical_stock
                )
            except (TypeError, ValueError):
                raise ValueError(
                    "physicalStock harus berupa angka."
                )

            if physical_stock < 0:
                raise ValueError(
                    "physicalStock tidak boleh negatif."
                )

            system_stock = (
                self.stock_movement_service
                .get_current_stock(product_id)
            )

            difference = (
                physical_stock - system_stock
            )

            processed_items.append({
                "productId": product_id,
                "systemStock": system_stock,
                "physicalStock": physical_stock,
                "difference": difference,
                "notes": item.get("notes", ""),
            })

        now = datetime.now(timezone.utc)

        opname_data = {
            "opnameNumber": opname_number,
            "opnameDate": now,
            "status": self.STATUS_DRAFT,
            "items": processed_items,
            "createdBy": created_by,
            "approvedBy": None,
            "createdAt": now,
            "updatedAt": now,
        }

        return self.repository.create(
            opname_data
        )

    def get_all_opnames(self):
        return self.repository.find_all()

    def get_opname_by_id(self, opname_id):
        return self.repository.find_by_id(
            opname_id
        )

    def submit_opname(self, opname_id):
        opname = self.repository.find_by_id(
            opname_id
        )

        if not opname:
            raise ValueError(
                "Stock opname tidak ditemukan."
            )

        if opname.get("status") != self.STATUS_DRAFT:
            raise ValueError(
                "Hanya opname dengan status DRAFT "
                "yang dapat disubmit."
            )

        return self.repository.update(
            opname_id,
            {
                "status": self.STATUS_SUBMITTED,
            },
        )

    def approve_opname(
        self,
        opname_id,
        approved_by=None,
    ):
        opname = self.repository.find_by_id(
            opname_id
        )

        if not opname:
            raise ValueError(
                "Stock opname tidak ditemukan."
            )

        if opname.get("status") != self.STATUS_SUBMITTED:
            raise ValueError(
                "Hanya opname dengan status SUBMITTED "
                "yang dapat disetujui."
            )

        for item in opname.get("items", []):
            difference = item.get(
                "difference",
                0
            )

            if difference == 0:
                continue

            self.stock_movement_service.create_movement(
                product_id=item["productId"],
                movement_type="ADJUSTMENT",
                quantity=abs(difference),
                reference_type="STOCK_OPNAME",
                reference_id=str(opname["_id"]),
                notes=(
                    f"Stock opname {opname['opnameNumber']}: "
                    f"{item['systemStock']} -> "
                    f"{item['physicalStock']}"
                ),
                created_by=approved_by,
                adjustment_quantity=difference,
            )

        return self.repository.update(
            opname_id,
            {
                "status": self.STATUS_APPROVED,
                "approvedBy": approved_by,
            },
        )