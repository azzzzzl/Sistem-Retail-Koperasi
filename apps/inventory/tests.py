from unittest.mock import MagicMock

from django.test import TestCase

from apps.inventory.services import StockMovementService
from apps.inventory.opname_services import StockOpnameService
from apps.inventory.adjustment_services import StockAdjustmentService
from apps.inventory.po_services import PurchaseOrderService
from apps.inventory.gr_services import GoodsReceiptService
from apps.inventory.purchase_services import PurchaseService
from apps.inventory.invoice_services import SupplierInvoiceService
from unittest.mock import MagicMock, patch


# ============================================================
# STOCK MOVEMENT
# ============================================================

class StockMovementServiceTestCase(TestCase):

    def setUp(self):
        self.service = StockMovementService()

        self.service.repository = MagicMock()

    def test_create_stock_in(self):
        self.service.repository.get_stock_balance.return_value = 0

        self.service.repository.create.side_effect = (
            lambda data: data
        )

        movement = self.service.create_movement(
            product_id="TEST-PRODUCT-001",
            movement_type="IN",
            quantity=10,
            reference_type="GOODS_RECEIPT",
            reference_id="TEST-GR-001",
            created_by="test-user",
        )

        self.assertEqual(
            movement["productId"],
            "TEST-PRODUCT-001",
        )

        self.assertEqual(
            movement["movementType"],
            "IN",
        )

        self.assertEqual(
            movement["quantity"],
            10,
        )

        self.assertEqual(
            movement["referenceType"],
            "GOODS_RECEIPT",
        )

    def test_create_stock_out(self):
        self.service.repository.get_stock_balance.return_value = 10

        self.service.repository.create.side_effect = (
            lambda data: data
        )

        movement = self.service.create_movement(
            product_id="TEST-PRODUCT-001",
            movement_type="OUT",
            quantity=4,
            reference_type="SALE",
            reference_id="TEST-SALE-001",
            created_by="test-user",
        )

        self.assertEqual(
            movement["movementType"],
            "OUT",
        )

        self.assertEqual(
            movement["quantity"],
            4,
        )

    def test_stock_out_cannot_exceed_stock(self):
        self.service.repository.get_stock_balance.return_value = 5

        with self.assertRaises(ValueError):
            self.service.create_movement(
                product_id="TEST-PRODUCT-001",
                movement_type="OUT",
                quantity=6,
                reference_type="SALE",
            )

    def test_quantity_must_be_positive(self):
        self.service.repository.get_stock_balance.return_value = 0

        with self.assertRaises(ValueError):
            self.service.create_movement(
                product_id="TEST-PRODUCT-001",
                movement_type="IN",
                quantity=0,
                reference_type="GOODS_RECEIPT",
            )

    def test_product_id_is_required(self):
        with self.assertRaises(ValueError):
            self.service.create_movement(
                product_id="",
                movement_type="IN",
                quantity=10,
                reference_type="GOODS_RECEIPT",
            )

    def test_invalid_movement_type(self):
        with self.assertRaises(ValueError):
            self.service.create_movement(
                product_id="TEST-PRODUCT-001",
                movement_type="INVALID",
                quantity=10,
                reference_type="GOODS_RECEIPT",
            )

    def test_stock_adjustment(self):
        self.service.repository.get_stock_balance.return_value = 5

        self.service.repository.create.side_effect = (
            lambda data: data
        )

        movement = self.service.create_movement(
            product_id="TEST-PRODUCT-001",
            movement_type="ADJUSTMENT",
            quantity=1,
            adjustment_quantity=3,
            reference_type="STOCK_ADJUSTMENT",
            reference_id="TEST-ADJ-001",
            created_by="test-user",
        )

        self.assertEqual(
            movement["movementType"],
            "ADJUSTMENT",
        )

        self.assertEqual(
            movement["adjustmentQuantity"],
            3,
        )

    def test_stock_adjustment_cannot_make_negative_stock(self):
        self.service.repository.get_stock_balance.return_value = 5

        with self.assertRaises(ValueError):
            self.service.create_movement(
                product_id="TEST-PRODUCT-001",
                movement_type="ADJUSTMENT",
                quantity=1,
                adjustment_quantity=-6,
                reference_type="STOCK_ADJUSTMENT",
            )


# ============================================================
# STOCK OPNAME
# ============================================================

class StockOpnameServiceTestCase(TestCase):

    def setUp(self):
        self.service = StockOpnameService()

        self.service.repository = MagicMock()
        self.service.stock_movement_service = MagicMock()

    def test_create_stock_opname(self):
        self.service.repository.find_by_number.return_value = None

        self.service.stock_movement_service.get_current_stock.return_value = 10

        self.service.repository.create.side_effect = (
            lambda data: data
        )

        opname = self.service.create_opname(
            opname_number="TEST-OPNAME-001",
            items=[
                {
                    "productId": "TEST-PRODUCT-001",
                    "physicalStock": 8,
                    "notes": "Selisih 2",
                }
            ],
            created_by="test-user",
        )

        self.assertEqual(
            opname["opnameNumber"],
            "TEST-OPNAME-001",
        )

        self.assertEqual(
            opname["status"],
            "DRAFT",
        )

        self.assertEqual(
            opname["items"][0]["systemStock"],
            10,
        )

        self.assertEqual(
            opname["items"][0]["physicalStock"],
            8,
        )

        self.assertEqual(
            opname["items"][0]["difference"],
            -2,
        )

    def test_opname_number_must_be_unique(self):
        self.service.repository.find_by_number.return_value = {
            "_id": "existing-opname"
        }

        with self.assertRaises(ValueError):
            self.service.create_opname(
                opname_number="TEST-OPNAME-001",
                items=[
                    {
                        "productId": "TEST-PRODUCT-001",
                        "physicalStock": 10,
                    }
                ],
            )

    def test_submit_stock_opname(self):
        self.service.repository.find_by_id.return_value = {
            "_id": "test-opname-id",
            "status": "DRAFT",
        }

        self.service.repository.update.return_value = {
            "_id": "test-opname-id",
            "status": "SUBMITTED",
        }

        result = self.service.submit_opname(
            "test-opname-id"
        )

        self.assertEqual(
            result["status"],
            "SUBMITTED",
        )

    def test_approve_stock_opname(self):
        self.service.repository.find_by_id.return_value = {
            "_id": "test-opname-id",
            "opnameNumber": "TEST-OPNAME-001",
            "status": "SUBMITTED",
            "items": [
                {
                    "productId": "TEST-PRODUCT-001",
                    "systemStock": 10,
                    "physicalStock": 8,
                    "difference": -2,
                }
            ],
        }

        self.service.repository.update.return_value = {
            "_id": "test-opname-id",
            "opnameNumber": "TEST-OPNAME-001",
            "status": "APPROVED",
        }

        result = self.service.approve_opname(
            "test-opname-id",
            approved_by="test-user",
        )

        self.assertEqual(
            result["status"],
            "APPROVED",
        )

        self.service.stock_movement_service.create_movement.assert_called_once()


# ============================================================
# STOCK ADJUSTMENT
# ============================================================

class StockAdjustmentServiceTestCase(TestCase):

    def setUp(self):
        self.service = StockAdjustmentService()

        self.service.repository = MagicMock()
        self.service.stock_movement_service = MagicMock()

        # Adjustment number baru dianggap belum pernah digunakan.
        self.service.repository.find_by_number.return_value = None

        # Stok awal default untuk test.
        self.service.stock_movement_service.get_current_stock.return_value = 10

    def test_increase_stock_adjustment(self):
        self.service.repository.create.return_value = {
            "_id": "test-adjustment-id-001",
            "adjustmentNumber": "TEST-ADJ-001",
            "productId": "TEST-PRODUCT-001",
            "adjustmentType": "INCREASE",
            "quantity": 3,
        }

        adjustment = self.service.create_adjustment(
            adjustment_number="TEST-ADJ-001",
            product_id="TEST-PRODUCT-001",
            adjustment_type="INCREASE",
            quantity=3,
            reason="Barang tambahan",
            created_by="test-user",
        )

        self.assertEqual(
            adjustment["_id"],
            "test-adjustment-id-001",
        )

        self.service.repository.create.assert_called_once()

        self.service.stock_movement_service.create_movement.assert_called_once()

    def test_decrease_stock_adjustment(self):
        self.service.repository.create.return_value = {
            "_id": "test-adjustment-id-002",
            "adjustmentNumber": "TEST-ADJ-002",
            "productId": "TEST-PRODUCT-001",
            "adjustmentType": "DECREASE",
            "quantity": 2,
        }

        adjustment = self.service.create_adjustment(
            adjustment_number="TEST-ADJ-002",
            product_id="TEST-PRODUCT-001",
            adjustment_type="DECREASE",
            quantity=2,
            reason="Barang rusak",
            created_by="test-user",
        )

        self.assertEqual(
            adjustment["_id"],
            "test-adjustment-id-002",
        )

        self.service.repository.create.assert_called_once()

        self.service.stock_movement_service.create_movement.assert_called_once()

    def test_decrease_stock_cannot_exceed_stock(self):
        self.service.repository.find_by_number.return_value = None

        self.service.stock_movement_service.get_current_stock.return_value = 5

        with self.assertRaises(ValueError):
            self.service.create_adjustment(
                adjustment_number="TEST-ADJ-003",
                product_id="TEST-PRODUCT-001",
                adjustment_type="DECREASE",
                quantity=999,
                reason="Test",
                created_by="test-user",
            )

# ============================================================
# PURCHASE ORDER
# ============================================================

class PurchaseOrderServiceTestCase(TestCase):

    def setUp(self):
        self.service = PurchaseOrderService()

        self.service.repository = MagicMock()

    def test_create_purchase_order(self):
        self.service.repository.find_by_number.return_value = None

        self.service.repository.create.side_effect = (
            lambda data: data
        )

        po = self.service.create_purchase_order(
            po_number="TEST-PO-001",
            supplier_id="TEST-SUPPLIER-001",
            items=[
                {
                    "productId": "TEST-PRODUCT-001",
                    "name": "Produk Test",
                    "quantity": 10,
                    "purchasePrice": 5000,
                }
            ],
            discount=5000,
            notes="Test PO",
            created_by="test-user",
        )

        self.assertEqual(
            po["status"],
            "DRAFT",
        )

        self.assertEqual(
            po["subtotal"],
            50000,
        )

        self.assertEqual(
            po["discount"],
            5000,
        )

        self.assertEqual(
            po["total"],
            45000,
        )

        self.assertEqual(
            po["items"][0]["quantity"],
            10,
        )

    def test_purchase_order_number_must_be_unique(self):
        self.service.repository.find_by_number.return_value = {
            "_id": "existing-po"
        }

        with self.assertRaises(ValueError):
            self.service.create_purchase_order(
                po_number="TEST-PO-001",
                supplier_id="TEST-SUPPLIER-001",
                items=[
                    {
                        "productId": "TEST-PRODUCT-001",
                        "name": "Produk Test",
                        "quantity": 10,
                        "purchasePrice": 5000,
                    }
                ],
            )

    def test_purchase_order_items_are_required(self):
        self.service.repository.find_by_number.return_value = None

        with self.assertRaises(ValueError):
            self.service.create_purchase_order(
                po_number="TEST-PO-002",
                supplier_id="TEST-SUPPLIER-001",
                items=[],
            )

    def test_quantity_must_be_positive(self):
        self.service.repository.find_by_number.return_value = None

        with self.assertRaises(ValueError):
            self.service.create_purchase_order(
                po_number="TEST-PO-003",
                supplier_id="TEST-SUPPLIER-001",
                items=[
                    {
                        "productId": "TEST-PRODUCT-001",
                        "name": "Produk Test",
                        "quantity": 0,
                        "purchasePrice": 5000,
                    }
                ],
            )

    def test_discount_cannot_exceed_subtotal(self):
        self.service.repository.find_by_number.return_value = None

        with self.assertRaises(ValueError):
            self.service.create_purchase_order(
                po_number="TEST-PO-004",
                supplier_id="TEST-SUPPLIER-001",
                items=[
                    {
                        "productId": "TEST-PRODUCT-001",
                        "name": "Produk Test",
                        "quantity": 10,
                        "purchasePrice": 5000,
                    }
                ],
                discount=60000,
            )

    def test_submit_purchase_order(self):
        self.service.repository.find_by_id.return_value = {
            "_id": "test-po-id",
            "status": "DRAFT",
        }

        self.service.repository.update.return_value = {
            "_id": "test-po-id",
            "status": "PENDING",
        }

        po = self.service.submit_purchase_order(
            "test-po-id"
        )

        self.assertEqual(
            po["status"],
            "PENDING",
        )

    def test_submit_only_draft_purchase_order(self):
        self.service.repository.find_by_id.return_value = {
            "_id": "test-po-id",
            "status": "APPROVED",
        }

        with self.assertRaises(ValueError):
            self.service.submit_purchase_order(
                "test-po-id"
            )

    def test_approve_purchase_order(self):
        self.service.repository.find_by_id.return_value = {
            "_id": "test-po-id",
            "status": "PENDING",
        }

        self.service.repository.update.return_value = {
            "_id": "test-po-id",
            "status": "APPROVED",
            "approvedBy": "test-user",
        }

        po = self.service.approve_purchase_order(
            "test-po-id",
            approved_by="test-user",
        )

        self.assertEqual(
            po["status"],
            "APPROVED",
        )

        self.assertEqual(
            po["approvedBy"],
            "test-user",
        )

    def test_only_pending_purchase_order_can_be_approved(self):
        self.service.repository.find_by_id.return_value = {
            "_id": "test-po-id",
            "status": "DRAFT",
        }

        with self.assertRaises(ValueError):
            self.service.approve_purchase_order(
                "test-po-id",
                approved_by="test-user",
            )

    def test_cancel_purchase_order(self):
        self.service.repository.find_by_id.return_value = {
            "_id": "test-po-id",
            "status": "PENDING",
        }

        self.service.repository.update.return_value = {
            "_id": "test-po-id",
            "status": "CANCELLED",
        }

        po = self.service.cancel_purchase_order(
            "test-po-id"
        )

        self.assertEqual(
            po["status"],
            "CANCELLED",
        )


# ============================================================
# GOODS RECEIPT
# ============================================================

class GoodsReceiptServiceTestCase(TestCase):

    def setUp(self):
        self.service = GoodsReceiptService()

        self.service.repository = MagicMock()
        self.service.po_repository = MagicMock()
        self.service.stock_movement_service = MagicMock()

        self.po = {
            "_id": "test-po-id",
            "poNumber": "TEST-PO-001",
            "supplierId": "TEST-SUPPLIER-001",
            "status": "APPROVED",
            "items": [
                {
                    "productId": "TEST-PRODUCT-001",
                    "name": "Produk Test",
                    "quantity": 10,
                    "purchasePrice": 5000,
                }
            ],
        }

    def test_create_goods_receipt(self):
        self.service.repository.find_by_number.return_value = None

        self.service.repository.find_by_po_id.return_value = []

        self.service.po_repository.find_by_id.return_value = (
            self.po
        )

        self.service.repository.create.side_effect = (
            lambda data: {
                **data,
                "_id": "test-receipt-id",
            }
        )

        receipt = self.service.create_goods_receipt(
            receipt_number="TEST-GR-001",
            po_id="test-po-id",
            items=[
                {
                    "productId": "TEST-PRODUCT-001",
                    "receivedQuantity": 10,
                    "acceptedQuantity": 8,
                    "rejectedQuantity": 2,
                }
            ],
            received_by="test-user",
        )

        self.assertEqual(
            receipt["receiptNumber"],
            "TEST-GR-001",
        )

        self.assertEqual(
            receipt["status"],
            "RECEIVED",
        )

        self.assertEqual(
            receipt["items"][0]["orderedQuantity"],
            10,
        )

        self.assertEqual(
            receipt["items"][0]["acceptedQuantity"],
            8,
        )

        self.service.stock_movement_service.create_movement.assert_called_once()

    def test_rejected_quantity_does_not_create_stock_movement(self):
        self.service.repository.find_by_number.return_value = None

        self.service.repository.find_by_po_id.return_value = []

        self.service.po_repository.find_by_id.return_value = (
            self.po
        )

        self.service.repository.create.side_effect = (
            lambda data: {
                **data,
                "_id": "test-receipt-id",
            }
        )

        self.service.create_goods_receipt(
            receipt_number="TEST-GR-002",
            po_id="test-po-id",
            items=[
                {
                    "productId": "TEST-PRODUCT-001",
                    "receivedQuantity": 2,
                    "acceptedQuantity": 0,
                    "rejectedQuantity": 2,
                }
            ],
            received_by="test-user",
        )

        self.service.stock_movement_service.create_movement.assert_not_called()

    def test_received_quantity_cannot_exceed_po_quantity(self):
        self.service.repository.find_by_number.return_value = None

        self.service.repository.find_by_po_id.return_value = []

        self.service.po_repository.find_by_id.return_value = (
            self.po
        )

        with self.assertRaises(ValueError):
            self.service.create_goods_receipt(
                receipt_number="TEST-GR-003",
                po_id="test-po-id",
                items=[
                    {
                        "productId": "TEST-PRODUCT-001",
                        "receivedQuantity": 11,
                        "acceptedQuantity": 11,
                        "rejectedQuantity": 0,
                    }
                ],
                received_by="test-user",
            )

    def test_accepted_plus_rejected_must_equal_received(self):
        self.service.repository.find_by_number.return_value = None

        self.service.repository.find_by_po_id.return_value = []

        self.service.po_repository.find_by_id.return_value = (
            self.po
        )

        with self.assertRaises(ValueError):
            self.service.create_goods_receipt(
                receipt_number="TEST-GR-004",
                po_id="test-po-id",
                items=[
                    {
                        "productId": "TEST-PRODUCT-001",
                        "receivedQuantity": 10,
                        "acceptedQuantity": 8,
                        "rejectedQuantity": 1,
                    }
                ],
                received_by="test-user",
            )

    def test_goods_receipt_requires_approved_or_partial_po(self):
        pending_po = {
            **self.po,
            "status": "PENDING",
        }

        self.service.repository.find_by_number.return_value = None

        self.service.po_repository.find_by_id.return_value = pending_po

        with self.assertRaises(ValueError):
            self.service.create_goods_receipt(
                receipt_number="TEST-GR-005",
                po_id="test-po-id",
                items=[
                    {
                        "productId": "TEST-PRODUCT-001",
                        "receivedQuantity": 5,
                        "acceptedQuantity": 5,
                        "rejectedQuantity": 0,
                    }
                ],
                received_by="test-user",
            )

    def test_partial_receipt(self):
        self.service.repository.find_by_number.return_value = None

        self.service.repository.find_by_po_id.return_value = []

        self.service.po_repository.find_by_id.return_value = (
            self.po
        )

        self.service.repository.create.side_effect = (
            lambda data: {
                **data,
                "_id": "test-receipt-id",
            }
        )

        receipt = self.service.create_goods_receipt(
            receipt_number="TEST-GR-006",
            po_id="test-po-id",
            items=[
                {
                    "productId": "TEST-PRODUCT-001",
                    "receivedQuantity": 4,
                    "acceptedQuantity": 4,
                    "rejectedQuantity": 0,
                }
            ],
            received_by="test-user",
        )

        self.assertEqual(
            receipt["items"][0]["receivedQuantity"],
            4,
        )

        self.service.stock_movement_service.create_movement.assert_called_once()


# ============================================================
# PURCHASE / PEMBELIAN
# ============================================================

class PurchaseServiceTestCase(TestCase):

    def setUp(self):
        self.service = PurchaseService()

        self.service.repository = MagicMock()
        self.service.po_repository = MagicMock()
        self.service.receipt_repository = MagicMock()

        self.po = {
            "_id": "test-po-id",
            "poNumber": "TEST-PO-001",
            "supplierId": "TEST-SUPPLIER-001",
        }

        self.receipt = {
            "_id": "test-receipt-id",
            "poId": "test-po-id",
            "supplierId": "TEST-SUPPLIER-001",
            "items": [
                {
                    "productId": "TEST-PRODUCT-001",
                    "acceptedQuantity": 8,
                    "rejectedQuantity": 2,
                    "purchasePrice": 5000,
                }
            ],
        }

    def test_create_purchase(self):
        self.service.repository.find_by_number.return_value = None

        self.service.repository.find_by_goods_receipt_id.return_value = []

        self.service.po_repository.find_by_id.return_value = (
            self.po
        )

        self.service.receipt_repository.find_by_id.return_value = (
            self.receipt
        )

        self.service.repository.create.side_effect = (
            lambda data: data
        )

        purchase = self.service.create_purchase(
            purchase_number="TEST-PURCHASE-001",
            po_id="test-po-id",
            goods_receipt_id="test-receipt-id",
            discount=5000,
            tax=2000,
            created_by="test-user",
        )

        self.assertEqual(
            purchase["paymentStatus"],
            "UNPAID",
        )

        self.assertEqual(
            purchase["subtotal"],
            40000,
        )

        self.assertEqual(
            purchase["discount"],
            5000,
        )

        self.assertEqual(
            purchase["tax"],
            2000,
        )

        self.assertEqual(
            purchase["total"],
            37000,
        )

        self.assertEqual(
            purchase["items"][0]["quantity"],
            8,
        )

    def test_purchase_number_must_be_unique(self):
        self.service.repository.find_by_number.return_value = {
            "_id": "existing-purchase"
        }

        with self.assertRaises(ValueError):
            self.service.create_purchase(
                purchase_number="TEST-PURCHASE-001",
                po_id="test-po-id",
                goods_receipt_id="test-receipt-id",
            )

    def test_goods_receipt_must_exist(self):
        self.service.repository.find_by_number.return_value = None

        self.service.po_repository.find_by_id.return_value = (
            self.po
        )

        self.service.receipt_repository.find_by_id.return_value = None

        with self.assertRaises(ValueError):
            self.service.create_purchase(
                purchase_number="TEST-PURCHASE-002",
                po_id="test-po-id",
                goods_receipt_id="not-found",
            )

    def test_goods_receipt_must_belong_to_po(self):
        self.service.repository.find_by_number.return_value = None

        self.service.po_repository.find_by_id.return_value = (
            self.po
        )

        wrong_receipt = {
            **self.receipt,
            "poId": "different-po-id",
        }

        self.service.receipt_repository.find_by_id.return_value = (
            wrong_receipt
        )

        with self.assertRaises(ValueError):
            self.service.create_purchase(
                purchase_number="TEST-PURCHASE-003",
                po_id="test-po-id",
                goods_receipt_id="test-receipt-id",
            )

    def test_goods_receipt_cannot_be_used_twice(self):
        self.service.repository.find_by_number.return_value = None

        self.service.po_repository.find_by_id.return_value = (
            self.po
        )

        self.service.receipt_repository.find_by_id.return_value = (
            self.receipt
        )

        self.service.repository.find_by_goods_receipt_id.return_value = [
            {
                "_id": "existing-purchase"
            }
        ]

        with self.assertRaises(ValueError):
            self.service.create_purchase(
                purchase_number="TEST-PURCHASE-004",
                po_id="test-po-id",
                goods_receipt_id="test-receipt-id",
            )

    def test_discount_cannot_exceed_subtotal(self):
        self.service.repository.find_by_number.return_value = None

        self.service.po_repository.find_by_id.return_value = (
            self.po
        )

        self.service.receipt_repository.find_by_id.return_value = (
            self.receipt
        )

        self.service.repository.find_by_goods_receipt_id.return_value = []

        with self.assertRaises(ValueError):
            self.service.create_purchase(
                purchase_number="TEST-PURCHASE-005",
                po_id="test-po-id",
                goods_receipt_id="test-receipt-id",
                discount=50000,
            )

    def test_purchase_requires_accepted_item(self):
        self.service.repository.find_by_number.return_value = None

        self.service.po_repository.find_by_id.return_value = (
            self.po
        )

        receipt = {
            **self.receipt,
            "items": [
                {
                    "productId": "TEST-PRODUCT-001",
                    "acceptedQuantity": 0,
                    "rejectedQuantity": 2,
                    "purchasePrice": 5000,
                }
            ],
        }

        self.service.receipt_repository.find_by_id.return_value = (
            receipt
        )

        self.service.repository.find_by_goods_receipt_id.return_value = []

        with self.assertRaises(ValueError):
            self.service.create_purchase(
                purchase_number="TEST-PURCHASE-006",
                po_id="test-po-id",
                goods_receipt_id="test-receipt-id",
            )

# ============================================================
# SUPPLIER INVOICE
# ============================================================

class SupplierInvoiceServiceTestCase(TestCase):

    def setUp(self):
        self.service = SupplierInvoiceService()

        self.service.repository = MagicMock()
        self.service.purchase_repository = MagicMock()

        self.purchase = {
            "_id": "test-purchase-id",
            "purchaseNumber": "TEST-PURCHASE-001",
            "supplierId": "TEST-SUPPLIER-001",
            "subtotal": 40000,
            "tax": 2000,
            "total": 42000,
        }

    def test_create_supplier_invoice(self):
        self.service.repository.find_by_number.return_value = None
        self.service.repository.find_by_purchase_id.return_value = []

        self.service.purchase_repository.find_by_id.return_value = (
            self.purchase
        )

        self.service.repository.create.side_effect = (
            lambda data: {
                **data,
                "_id": "test-invoice-id",
            }
        )

        invoice = self.service.create_invoice(
            invoice_number="TEST-INVOICE-001",
            purchase_id="test-purchase-id",
            due_date="2026-10-30T00:00:00+00:00",
            created_by="test-user",
        )

        self.assertEqual(
            invoice["_id"],
            "test-invoice-id",
        )

        self.assertEqual(
            invoice["supplierId"],
            "TEST-SUPPLIER-001",
        )

        self.assertEqual(
            invoice["purchaseId"],
            "test-purchase-id",
        )

        self.assertEqual(
            invoice["subtotal"],
            40000,
        )

        self.assertEqual(
            invoice["tax"],
            2000,
        )

        self.assertEqual(
            invoice["total"],
            42000,
        )

        self.assertEqual(
            invoice["paidAmount"],
            0,
        )

        self.assertEqual(
            invoice["remainingAmount"],
            42000,
        )

        self.assertEqual(
            invoice["status"],
            "UNPAID",
        )

    def test_invoice_number_must_be_unique(self):
        self.service.repository.find_by_number.return_value = {
            "_id": "existing-invoice"
        }

        with self.assertRaises(ValueError):
            self.service.create_invoice(
                invoice_number="TEST-INVOICE-001",
                purchase_id="test-purchase-id",
            )

    def test_purchase_must_exist(self):
        self.service.repository.find_by_number.return_value = None

        self.service.purchase_repository.find_by_id.return_value = None

        with self.assertRaises(ValueError):
            self.service.create_invoice(
                invoice_number="TEST-INVOICE-002",
                purchase_id="not-found",
            )

    def test_purchase_can_have_only_one_invoice(self):
        self.service.repository.find_by_number.return_value = None

        self.service.purchase_repository.find_by_id.return_value = (
            self.purchase
        )

        self.service.repository.find_by_purchase_id.return_value = [
            {
                "_id": "existing-invoice"
            }
        ]

        with self.assertRaises(ValueError):
            self.service.create_invoice(
                invoice_number="TEST-INVOICE-003",
                purchase_id="test-purchase-id",
            )

    def test_invoice_total_must_match_subtotal_plus_tax(self):
        self.service.repository.find_by_number.return_value = None

        invalid_purchase = {
            **self.purchase,
            "total": 50000,
        }

        self.service.purchase_repository.find_by_id.return_value = (
            invalid_purchase
        )

        self.service.repository.find_by_purchase_id.return_value = []

        with self.assertRaises(ValueError):
            self.service.create_invoice(
                invoice_number="TEST-INVOICE-004",
                purchase_id="test-purchase-id",
            )

    def test_due_date_cannot_be_before_invoice_date(self):
        self.service.repository.find_by_number.return_value = None

        self.service.purchase_repository.find_by_id.return_value = (
            self.purchase
        )

        self.service.repository.find_by_purchase_id.return_value = []

        with self.assertRaises(ValueError):
            self.service.create_invoice(
                invoice_number="TEST-INVOICE-005",
                purchase_id="test-purchase-id",
                invoice_date="2026-10-20T00:00:00+00:00",
                due_date="2026-10-19T00:00:00+00:00",
            )

    def test_update_payment_status_to_partial(self):
        self.service.repository.find_by_id.return_value = {
            "_id": "test-invoice-id",
            "total": 42000,
            "paidAmount": 0,
            "remainingAmount": 42000,
            "status": "UNPAID",
        }

        self.service.repository.update.return_value = {
            "_id": "test-invoice-id",
            "total": 42000,
            "paidAmount": 20000,
            "remainingAmount": 22000,
            "status": "PARTIAL",
        }

        invoice = self.service.update_payment_status(
            "test-invoice-id",
            20000,
        )

        self.assertEqual(
            invoice["paidAmount"],
            20000,
        )

        self.assertEqual(
            invoice["remainingAmount"],
            22000,
        )

        self.assertEqual(
            invoice["status"],
            "PARTIAL",
        )

    def test_payment_cannot_exceed_invoice_total(self):
        self.service.repository.find_by_id.return_value = {
            "_id": "test-invoice-id",
            "total": 42000,
        }

        with self.assertRaises(ValueError):
            self.service.update_payment_status(
                "test-invoice-id",
                42001,
            )

class SupplierPaymentServiceTestCase(TestCase):

    def setUp(self):
        from unittest.mock import MagicMock

        from apps.inventory.payment_services import (
            SupplierPaymentService,
        )

        self.service = SupplierPaymentService()

        self.service.repository = MagicMock()
        self.service.invoice_repository = MagicMock()

    def test_create_payment_partial(self):
        invoice_id = "test-invoice-id"

        self.service.repository.find_by_number.return_value = None

        self.service.invoice_repository.find_by_id.return_value = {
            "_id": invoice_id,
            "supplierId": "TEST-SUPPLIER-001",
            "total": 1000000,
            "paidAmount": 0,
            "remainingAmount": 1000000,
            "status": "UNPAID",
        }

        self.service.repository.create.return_value = {
            "_id": "test-payment-id",
            "paymentNumber": "TEST-PAY-001",
            "invoiceId": invoice_id,
            "amount": 400000,
        }

        self.service.invoice_repository.update.return_value = {
            "_id": invoice_id,
            "total": 1000000,
            "paidAmount": 400000,
            "remainingAmount": 600000,
            "status": "PARTIAL",
        }

        result = self.service.create_payment(
            payment_number="TEST-PAY-001",
            invoice_id=invoice_id,
            amount=400000,
            payment_method="TRANSFER",
            created_by="test-user",
        )

        self.assertEqual(
            result["invoice"]["paidAmount"],
            400000,
        )

        self.assertEqual(
            result["invoice"]["remainingAmount"],
            600000,
        )

        self.assertEqual(
            result["invoice"]["status"],
            "PARTIAL",
        )

    def test_create_payment_full(self):
        invoice_id = "test-invoice-id"

        self.service.repository.find_by_number.return_value = None

        self.service.invoice_repository.find_by_id.return_value = {
            "_id": invoice_id,
            "supplierId": "TEST-SUPPLIER-001",
            "total": 1000000,
            "paidAmount": 0,
            "remainingAmount": 1000000,
            "status": "UNPAID",
        }

        self.service.repository.create.return_value = {
            "_id": "test-payment-id",
            "paymentNumber": "TEST-PAY-002",
            "invoiceId": invoice_id,
            "amount": 1000000,
        }

        self.service.invoice_repository.update.return_value = {
            "_id": invoice_id,
            "total": 1000000,
            "paidAmount": 1000000,
            "remainingAmount": 0,
            "status": "PAID",
        }

        result = self.service.create_payment(
            payment_number="TEST-PAY-002",
            invoice_id=invoice_id,
            amount=1000000,
            payment_method="TRANSFER",
            created_by="test-user",
        )

        self.assertEqual(
            result["invoice"]["paidAmount"],
            1000000,
        )

        self.assertEqual(
            result["invoice"]["remainingAmount"],
            0,
        )

        self.assertEqual(
            result["invoice"]["status"],
            "PAID",
        )

    def test_payment_number_must_be_unique(self):
        self.service.repository.find_by_number.return_value = {
            "_id": "existing-payment",
            "paymentNumber": "TEST-PAY-003",
        }

        with self.assertRaises(ValueError):
            self.service.create_payment(
                payment_number="TEST-PAY-003",
                invoice_id="test-invoice-id",
                amount=100000,
            )

    def test_invoice_must_exist(self):
        self.service.repository.find_by_number.return_value = None

        self.service.invoice_repository.find_by_id.return_value = None

        with self.assertRaises(ValueError):
            self.service.create_payment(
                payment_number="TEST-PAY-004",
                invoice_id="not-found",
                amount=100000,
            )

    def test_payment_amount_must_be_positive(self):
        self.service.repository.find_by_number.return_value = None

        self.service.invoice_repository.find_by_id.return_value = {
            "_id": "test-invoice-id",
            "supplierId": "TEST-SUPPLIER-001",
            "total": 1000000,
            "paidAmount": 0,
            "remainingAmount": 1000000,
            "status": "UNPAID",
        }

        with self.assertRaises(ValueError):
            self.service.create_payment(
                payment_number="TEST-PAY-005",
                invoice_id="test-invoice-id",
                amount=0,
            )

    def test_payment_cannot_exceed_remaining_amount(self):
        self.service.repository.find_by_number.return_value = None

        self.service.invoice_repository.find_by_id.return_value = {
            "_id": "test-invoice-id",
            "supplierId": "TEST-SUPPLIER-001",
            "total": 1000000,
            "paidAmount": 700000,
            "remainingAmount": 300000,
            "status": "PARTIAL",
        }

        with self.assertRaises(ValueError):
            self.service.create_payment(
                payment_number="TEST-PAY-006",
                invoice_id="test-invoice-id",
                amount=300001,
            )

    def test_invalid_payment_method(self):
        self.service.repository.find_by_number.return_value = None

        self.service.invoice_repository.find_by_id.return_value = {
            "_id": "test-invoice-id",
            "supplierId": "TEST-SUPPLIER-001",
            "total": 1000000,
            "paidAmount": 0,
            "remainingAmount": 1000000,
            "status": "UNPAID",
        }

        with self.assertRaises(ValueError):
            self.service.create_payment(
                payment_number="TEST-PAY-007",
                invoice_id="test-invoice-id",
                amount=100000,
                payment_method="INVALID",
            )

    def test_payment_uses_invoice_supplier_id(self):
        invoice_id = "test-invoice-id"

        self.service.repository.find_by_number.return_value = None

        self.service.invoice_repository.find_by_id.return_value = {
            "_id": invoice_id,
            "supplierId": "TEST-SUPPLIER-999",
            "total": 500000,
            "paidAmount": 0,
            "remainingAmount": 500000,
            "status": "UNPAID",
        }

        self.service.repository.create.return_value = {
            "_id": "test-payment-id",
            "paymentNumber": "TEST-PAY-008",
            "invoiceId": invoice_id,
            "supplierId": "TEST-SUPPLIER-999",
            "amount": 100000,
        }

        self.service.invoice_repository.update.return_value = {
            "_id": invoice_id,
            "total": 500000,
            "paidAmount": 100000,
            "remainingAmount": 400000,
            "status": "PARTIAL",
        }

        self.service.create_payment(
            payment_number="TEST-PAY-008",
            invoice_id=invoice_id,
            amount=100000,
        )

        created_payment = (
            self.service.repository.create.call_args[0][0]
        )

        self.assertEqual(
            created_payment["supplierId"],
            "TEST-SUPPLIER-999",
        )

    def test_payment_updates_invoice(self):
        invoice_id = "test-invoice-id"

        self.service.repository.find_by_number.return_value = None

        self.service.invoice_repository.find_by_id.return_value = {
            "_id": invoice_id,
            "supplierId": "TEST-SUPPLIER-001",
            "total": 1000000,
            "paidAmount": 200000,
            "remainingAmount": 800000,
            "status": "PARTIAL",
        }

        self.service.repository.create.return_value = {
            "_id": "test-payment-id",
            "paymentNumber": "TEST-PAY-009",
            "invoiceId": invoice_id,
            "amount": 300000,
        }

        self.service.invoice_repository.update.return_value = {
            "_id": invoice_id,
            "total": 1000000,
            "paidAmount": 500000,
            "remainingAmount": 500000,
            "status": "PARTIAL",
        }

        self.service.create_payment(
            payment_number="TEST-PAY-009",
            invoice_id=invoice_id,
            amount=300000,
        )

        self.service.invoice_repository.update.assert_called_once()

        update_args = (
            self.service.invoice_repository.update.call_args
        )

        self.assertEqual(
            update_args[0][0],
            invoice_id,
        )

        update_data = update_args[0][1]

        self.assertEqual(
            update_data["paidAmount"],
            500000,
        )

        self.assertEqual(
            update_data["remainingAmount"],
            500000,
        )

        self.assertEqual(
            update_data["status"],
            "PARTIAL",
        )

class SupplierDebtServiceTestCase(TestCase):

    def setUp(self):
        from unittest.mock import MagicMock

        from apps.inventory.debt_services import (
            SupplierDebtService,
        )

        self.service = SupplierDebtService()

        self.service.invoice_repository = MagicMock()

    def test_get_supplier_debt(self):
        supplier_id = "TEST-SUPPLIER-001"

        self.service.invoice_repository.find_by_supplier_id.return_value = [
            {
                "_id": "invoice-001",
                "invoiceNumber": "INV-001",
                "supplierId": supplier_id,
                "invoiceDate": "2026-09-01",
                "dueDate": "2026-09-30",
                "total": 1000000,
                "paidAmount": 400000,
                "remainingAmount": 600000,
                "status": "PARTIAL",
            },
            {
                "_id": "invoice-002",
                "invoiceNumber": "INV-002",
                "supplierId": supplier_id,
                "invoiceDate": "2026-09-05",
                "dueDate": "2026-10-05",
                "total": 500000,
                "paidAmount": 0,
                "remainingAmount": 500000,
                "status": "UNPAID",
            },
        ]

        result = self.service.get_supplier_debt(
            supplier_id
        )

        self.assertEqual(
            result["supplierId"],
            supplier_id,
        )

        self.assertEqual(
            result["invoiceCount"],
            2,
        )

        self.assertEqual(
            result["totalAmount"],
            1500000,
        )

        self.assertEqual(
            result["totalPaid"],
            400000,
        )

        self.assertEqual(
            result["totalDebt"],
            1100000,
        )

        self.assertEqual(
            len(result["invoices"]),
            2,
        )

    def test_get_supplier_debt_requires_supplier_id(self):
        with self.assertRaises(ValueError):
            self.service.get_supplier_debt("")

    def test_get_supplier_debt_without_invoices(self):
        self.service.invoice_repository.find_by_supplier_id.return_value = []

        result = self.service.get_supplier_debt(
            "TEST-SUPPLIER-EMPTY"
        )

        self.assertEqual(
            result["invoiceCount"],
            0,
        )

        self.assertEqual(
            result["totalAmount"],
            0,
        )

        self.assertEqual(
            result["totalPaid"],
            0,
        )

        self.assertEqual(
            result["totalDebt"],
            0,
        )

        self.assertEqual(
            result["invoices"],
            [],
        )

    def test_get_outstanding_invoices(self):
        supplier_id = "TEST-SUPPLIER-001"

        self.service.invoice_repository.find_by_supplier_id.return_value = [
            {
                "_id": "invoice-001",
                "invoiceNumber": "INV-001",
                "supplierId": supplier_id,
                "total": 1000000,
                "paidAmount": 400000,
                "remainingAmount": 600000,
                "status": "PARTIAL",
            },
            {
                "_id": "invoice-002",
                "invoiceNumber": "INV-002",
                "supplierId": supplier_id,
                "total": 500000,
                "paidAmount": 500000,
                "remainingAmount": 0,
                "status": "PAID",
            },
        ]

        result = (
            self.service.get_all_outstanding_invoices(
                supplier_id
            )
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertEqual(
            result[0]["invoiceNumber"],
            "INV-001",
        )

        self.assertEqual(
            result[0]["remainingAmount"],
            600000,
        )

    def test_get_outstanding_invoices_all_suppliers(self):
        self.service.invoice_repository.find_all.return_value = [
            {
                "_id": "invoice-001",
                "invoiceNumber": "INV-001",
                "supplierId": "SUP-001",
                "total": 1000000,
                "paidAmount": 0,
                "remainingAmount": 1000000,
                "status": "UNPAID",
            },
            {
                "_id": "invoice-002",
                "invoiceNumber": "INV-002",
                "supplierId": "SUP-002",
                "total": 500000,
                "paidAmount": 500000,
                "remainingAmount": 0,
                "status": "PAID",
            },
        ]

        result = (
            self.service.get_all_outstanding_invoices()
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertEqual(
            result[0]["supplierId"],
            "SUP-001",
        )

        self.service.invoice_repository.find_all.assert_called_once()

    def test_outstanding_invoice_excludes_zero_remaining(self):
        self.service.invoice_repository.find_all.return_value = [
            {
                "_id": "invoice-paid",
                "invoiceNumber": "INV-PAID",
                "supplierId": "SUP-001",
                "total": 100000,
                "paidAmount": 100000,
                "remainingAmount": 0,
                "status": "PAID",
            },
        ]

        result = (
            self.service.get_all_outstanding_invoices()
        )

        self.assertEqual(
            result,
            [],
        )