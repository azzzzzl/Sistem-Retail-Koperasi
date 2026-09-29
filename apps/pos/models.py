from decimal import Decimal

from django.db import models
from django.utils import timezone


class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True, db_index=True)
    barcode = models.CharField(max_length=100, blank=True, db_index=True)
    selling_price = models.DecimalField(max_digits=14, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Penjualan(models.Model):
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_CHOICES = ((STATUS_COMPLETED, "Selesai"), (STATUS_CANCELLED, "Dibatalkan"))

    no_nota = models.CharField(max_length=32, unique=True, db_column="invoice_number")
    tanggal = models.DateTimeField(default=timezone.now, db_column="created_at", db_index=True)
    kasir_id = models.CharField(max_length=64, db_index=True)
    kasir_nama = models.CharField(max_length=150)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    diskon = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    bayar = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    kembalian = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    metode_bayar = models.CharField(max_length=20, default="CASH")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_COMPLETED)

    class Meta:
        db_table = "sales"
        ordering = ("-tanggal",)

    def __str__(self):
        return self.no_nota


class DetailPenjualan(models.Model):
    transaksi = models.ForeignKey(Penjualan, on_delete=models.PROTECT, related_name="detail")
    produk = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="detail_penjualan")
    nama_produk = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True)
    harga = models.DecimalField(max_digits=14, decimal_places=2)
    qty = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        db_table = "sale_items"

    def __str__(self):
        return f"{self.transaksi.no_nota} - {self.nama_produk}"


class ReturPenjualan(models.Model):
    transaksi = models.ForeignKey(Penjualan, on_delete=models.PROTECT, related_name="retur")
    detail = models.ForeignKey(DetailPenjualan, on_delete=models.PROTECT, related_name="retur")
    qty = models.PositiveIntegerField()
    alasan = models.CharField(max_length=120)
    dibuat_oleh = models.CharField(max_length=150)
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sales_returns"