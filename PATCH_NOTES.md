# Patch Notes — Sistem Retail Koperasi

Project ini sudah diperbaiki dari baseline yang diberikan tanpa menghapus modul yang sudah benar.

## Perbaikan utama

- Dashboard analytics sekarang terhubung ke halaman `/dashboard/`.
- Reports memiliki halaman HTML dan tetap mendukung JSON melalui `?format=json`.
- Laporan sales, purchase, inventory, supplier, payables, profit, dan audit sudah tersedia.
- Export Excel/PDF ditambahkan untuk laporan yang relevan.
- Procurement dan inventory memiliki UI Django Template selain endpoint JSON.
- Seluruh endpoint procurement/inventory diberi pengecekan permission server-side.
- Perubahan stok menggunakan conditional atomic update untuk mencegah stok negatif dan race condition sederhana.
- Stock movement menyimpan before/after stock dan memiliki rollback kompensasi ketika pencatatan gagal.
- Stok awal produk dicatat sebagai `OPENING_BALANCE`; perubahan stok dari form produk menjadi stock adjustment/movement.
- Checkout POS memvalidasi stok terbaru, menyimpan purchase/cost snapshot, dan memiliki rollback kompensasi jika salah satu tahap gagal.
- POS mendukung CASH, TRANSFER, QRIS, dan OTHER serta diskon, pajak, anggota, referensi pembayaran, dan pembatalan transaksi.
- Retur penjualan dan retur pembelian memakai status `PENDING`/`PROCESSING`/`APPROVED` agar stok baru dikembalikan setelah approval.
- Supplier payment dan invoice menggunakan update conditional agar jumlah pembayaran tidak melebihi sisa invoice.
- Sinkronisasi status pembayaran purchase diperbaiki.
- Invoice purchase memperhitungkan discount + tax saat memvalidasi total.
- Tanggal dari endpoint procurement/payment dinormalisasi ke datetime timezone-aware.
- Audit log menggunakan field canonical `module`, `referenceId`, `before`, dan `after` sambil mempertahankan alias lama untuk kompatibilitas data.
- Purchase return, expenses, expense detail/edit, dan root aliases sesuai URL PRD ditambahkan.
- Master-data delete memakai soft-delete untuk menjaga histori transaksi.
- Validasi master data diperkuat pada sisi server.
- MongoDB index bootstrap ditambahkan dan indeks legacy dibuat sparse agar tidak memblokir data baru.
- `.env.example`, `scripts/init_mongodb.py`, `scripts/verify_project.py`, requirements pinned, dan README setup diperbarui.
- File cache Python dan `Pipfile.lock` stale tidak disertakan.

## Verifikasi yang dilakukan di lingkungan build

- Semua file Python berhasil diparse dengan AST: 0 error.
- `python -m compileall -q .` berhasil.
- Seluruh template yang direferensikan dari `render()` tersedia.
- Semua template laporan utama tersedia.
- Tidak ada `.pyc`/`__pycache__` di paket final.
- `.env` tidak disertakan.

## Catatan runtime

Lingkungan build ini tidak memiliki akses internet dan dependency Django/PyMongo tidak dapat di-install dari PyPI. Karena itu `python manage.py check` dan suite test berbasis MongoDB tidak dapat dieksekusi di lingkungan build ini.

Setelah ZIP dipindahkan ke komputer pengembangan, install `requirements.txt`, pastikan MongoDB aktif, lalu jalankan:

```text
python scripts/init_mongodb.py
python scripts/verify_project.py
python manage.py test
python manage.py runserver
```

Smoke test pertama:

```text
http://127.0.0.1:8000/health/
```

## Rebuild verification tambahan

- Ditambahkan alias UI root `/returns/`, `/returns/sales/`, dan `/returns/purchases/` agar sesuai halaman PRD.
- Ditambahkan halaman supplier untuk produk, purchase order, invoice, dan pembayaran.
- User creation sekarang dilindungi decorator permission yang sama dengan modul user management lainnya.
- Retur penjualan mendapatkan `returnNumber`, `createdBy`, `memberId`, `reason`, `refundAmount`, dan status refund. Approval membuat catatan refund terpisah dan hanya menambah stok ketika produk boleh di-restock.
- PosCartService diperbaiki agar memakai PosProductRepository yang benar.
- Ditambahkan unique index untuk `returns.returnNumber`.
