# Sistem Retail Koperasi — Django + MongoDB

Aplikasi web toko koperasi berbasis Django Templates, Python, dan MongoDB/PyMongo.

## Modul
Authentication, user management, master data (produk/kategori/supplier/anggota/produk supplier), procurement, inventory, POS/penjualan, retur, pengeluaran, laporan, dan audit log.

## Pemeriksaan cepat
Setelah server berjalan, buka `http://127.0.0.1:8000/health/`. Respons JSON dengan `success: true` dan `status: ok` menandakan Django hidup.

## Instalasi
1. Pastikan Python 3.13+ dan MongoDB aktif.
2. Buat virtual environment: `python -m venv .venv` lalu aktifkan.
3. Install dependency: `pip install -r requirements.txt`.
4. Salin `.env.example` menjadi `.env` lalu sesuaikan konfigurasi.
5. Jalankan `python scripts/init_mongodb.py` untuk membuat index.
6. Jalankan `python scripts/create_admin.py`.
7. Jalankan `python manage.py runserver`.
8. Buka `http://127.0.0.1:8000/login/`.

## Akun awal
Username: `admin`
Password: `Admin12345`
Ganti password setelah login. Password dapat diubah via `ADMIN_PASSWORD` untuk environment sendiri.

## URL UI
`/dashboard/`, `/products/`, `/categories/`, `/suppliers/`, `/members/`, `/purchase-orders/`, `/goods-receipts/`, `/purchases/`, `/supplier-invoices/`, `/supplier-payments/`, `/inventory/`, `/inventory/stock-opname/`, `/pos/`, `/sales/`, `/returns/`, `/expenses/`, `/reports/`, `/reports/sales/`, `/reports/purchases/`, `/reports/inventory/`, `/reports/suppliers/`, `/reports/payables/`, `/reports/profit/`, `/audit-logs/`.

Raw inventory/procurement JSON endpoints tersedia di `/api/inventory/`.

## Export
Laporan penjualan, pembelian, inventory, supplier, dan hutang dapat diekspor ke Excel/PDF.

## Testing
`python manage.py test`. Test membutuhkan dependency yang terpasang dan MongoDB sesuai `.env`.

## Data integrity
Perubahan stok melalui `StockMovementService`, stok keluar menggunakan conditional atomic update, pembayaran supplier menggunakan conditional invoice update, dan retur memakai status `PENDING` → `APPROVED` sebelum mengubah stok.


## Verifikasi
Setelah dependency terpasang dan MongoDB tersedia, jalankan `python scripts/verify_project.py`, lalu `python manage.py test`. Untuk instalasi baru, jalankan `python scripts/init_mongodb.py` sekali sebelum memakai aplikasi.

## Catatan data lama
Versi project ini menerima beberapa nama field lama (snake_case) saat membaca data untuk menjaga kompatibilitas, tetapi data/transaksi baru menggunakan field canonical camelCase yang konsisten dengan PRD.
