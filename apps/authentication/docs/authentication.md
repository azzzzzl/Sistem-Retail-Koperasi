# Dokumentasi Authentication & Authorization

## Sistem Informasi Toko Koperasi Berbasis Django dan MongoDB

## 1. Deskripsi

Modul Authentication & Authorization merupakan bagian dari sistem yang digunakan untuk mengatur proses autentikasi pengguna serta pembatasan akses terhadap fitur berdasarkan role dan permission.

Authentication digunakan untuk memastikan bahwa pengguna yang mengakses sistem merupakan pengguna yang telah terdaftar. Proses authentication meliputi login, validasi username dan password, pemeriksaan status akun, pembuatan session, dan logout.

Authorization digunakan untuk menentukan fitur yang dapat diakses oleh pengguna berdasarkan role dan permission yang dimilikinya. Pemeriksaan authorization dilakukan pada sisi server sehingga keamanan tidak hanya bergantung pada tampilan menu pada halaman aplikasi.

Sistem menggunakan Django Session Authentication dengan MongoDB sebagai penyimpanan data pengguna melalui PyMongo.

---

## 2. Role Pengguna

Sistem memiliki empat role pengguna, yaitu Admin, Kasir, Pengurus, dan Anggota.

| Role     | Deskripsi                                                                           |
| -------- | ----------------------------------------------------------------------------------- |
| Admin    | Mengelola pengguna dan memiliki akses terhadap berbagai fitur administrasi sistem.  |
| Kasir    | Mengelola transaksi penjualan, pembayaran, pencarian produk, dan riwayat transaksi. |
| Pengurus | Mengelola pengadaan, penerimaan barang, inventori, supplier, anggota, dan laporan.  |
| Anggota  | Mengakses informasi profil dan transaksi pribadi.                                   |

Role pengguna disimpan pada collection `users` di MongoDB pada field `role`.

Contoh struktur data role:

```text
role: "Admin"
```

Nilai role yang digunakan dalam sistem adalah:

```python
ROLES = [
    "Admin",
    "Kasir",
    "Pengurus",
    "Anggota"
]
```

---

## 3. Authentication

Authentication digunakan untuk memverifikasi identitas pengguna sebelum pengguna dapat mengakses fitur yang membutuhkan login.

Proses login dilakukan melalui halaman:

```text
/login/
```

Pengguna memasukkan:

* Username
* Password

Kemudian sistem melakukan beberapa proses:

1. Menerima username dan password dari form login.
2. Mencari user berdasarkan username pada collection `users`.
3. Mengambil `passwordHash` dari data user.
4. Memverifikasi password menggunakan mekanisme hashing Django.
5. Memeriksa status akun pengguna.
6. Jika password benar dan akun aktif, sistem membuat Django session.
7. Sistem mencatat aktivitas login pada audit log.
8. Pengguna diarahkan ke dashboard.

Jika username atau password salah, sistem menampilkan pesan:

```text
Username atau password salah.
```

Jika akun tidak aktif, sistem menampilkan:

```text
Akun tidak aktif.
```

---

## 4. Session

Setelah login berhasil, sistem membuat Django session untuk menyimpan informasi pengguna yang sedang login.

Data yang disimpan pada session meliputi:

```python
request.session["user_id"] = str(user["_id"])
request.session["username"] = user["username"]
request.session["name"] = user["name"]
request.session["role"] = user["role"]
```

Session digunakan untuk mengenali pengguna pada request berikutnya tanpa harus melakukan login kembali pada setiap halaman.

Informasi session tersebut juga digunakan dalam proses authorization untuk mengetahui role pengguna.

Contohnya:

```python
role = request.session.get("role")
```

Sistem menggunakan `user_id` pada session untuk menentukan apakah pengguna telah login.

---

## 5. Logout

Logout digunakan untuk mengakhiri sesi pengguna.

Endpoint logout:

```text
/logout/
```

Ketika pengguna melakukan logout, sistem melakukan proses berikut:

1. Mencatat aktivitas logout ke audit log.
2. Menghapus seluruh data session menggunakan `request.session.flush()`.
3. Mengarahkan pengguna kembali ke halaman login.

Implementasi logout:

```python
request.session.flush()
return redirect("/login/")
```

Dengan menggunakan `flush()`, data session pengguna yang sedang aktif dihapus sehingga session tersebut tidak dapat digunakan kembali setelah logout.

---

## 6. Authorization

Authorization digunakan untuk menentukan apakah pengguna memiliki izin untuk mengakses suatu fitur.

Sistem menggunakan permission yang dikaitkan dengan masing-masing role.

Permission untuk Admin meliputi:

```text
user_management
product_management
category_management
supplier_management
member_management
sales
procurement
inventory
reports
audit_log
```

Permission untuk Kasir:

```text
product_search
sales
payments
transaction_history
```

Permission untuk Pengurus:

```text
procurement
goods_receipt
inventory
supplier_management
member_management
reports
```

Permission untuk Anggota:

```text
profile
own_transactions
```

Pemeriksaan permission dilakukan pada server menggunakan decorator.

Contohnya:

```python
@permission_required_custom("user_management")
def user_list_view(request):
    ...
```

Jika pengguna tidak memiliki permission tersebut, server memberikan response:

```text
HTTP 403 Forbidden
```

Dengan demikian, pengguna tidak dapat memperoleh akses hanya dengan memasukkan URL secara langsung.

---

## 7. Decorator Authorization

Sistem memiliki beberapa decorator yang digunakan untuk membuat pemeriksaan akses dapat digunakan kembali pada berbagai view.

### 7.1 `login_required_custom`

Decorator ini digunakan untuk memastikan pengguna sudah login.

```python
@login_required_custom
def some_view(request):
    ...
```

Jika session `user_id` tidak ditemukan, pengguna diarahkan ke:

```text
/login/
```

### 7.2 `role_required`

Decorator ini digunakan untuk membatasi akses berdasarkan role tertentu.

Contoh:

```python
@role_required("Admin")
def some_view(request):
    ...
```

View tersebut hanya dapat diakses oleh pengguna dengan role Admin.

### 7.3 `permission_required_custom`

Decorator ini digunakan untuk membatasi akses berdasarkan permission.

Contoh:

```python
@permission_required_custom("user_management")
def user_list_view(request):
    ...
```

Decorator akan:

1. Memeriksa session pengguna.
2. Mengambil role dari session.
3. Memeriksa permission role tersebut.
4. Mengizinkan request jika memiliki permission.
5. Mengembalikan HTTP 403 jika tidak memiliki permission.

---

## 8. Manajemen User

Manajemen user digunakan oleh Admin untuk mengelola data pengguna sistem.

Halaman utama manajemen user:

```text
/users/
```

Fitur yang tersedia meliputi:

* Melihat daftar user.
* Membuat user baru.
* Melihat detail user.
* Mengubah data user.
* Mengaktifkan user.
* Menonaktifkan user.
* Reset password.
* Mengubah role user.

URL yang digunakan:

```text
/users/
/users/create/
/users/<id>/
/users/<id>/edit/
/users/<id>/status/
/users/<id>/reset-password/
/users/<id>/role/
```

Akses terhadap manajemen user menggunakan permission:

```text
user_management
```

Permission tersebut dimiliki oleh Admin.

Sistem tidak menyediakan penghapusan user secara langsung. Pendekatan ini digunakan agar data pengguna yang berkaitan dengan aktivitas atau transaksi tidak mudah dihapus.

---

## 9. Status User

Setiap user memiliki status yang menunjukkan apakah akun dapat digunakan untuk login.

Status yang digunakan:

```text
active
inactive
```

User dengan status:

```text
active
```

dapat melakukan login apabila username dan password benar.

Sedangkan user dengan status:

```text
inactive
```

tidak dapat melakukan login.

Pemeriksaan dilakukan pada proses login:

```python
if user.get("status") != "active":
    return None, "Akun tidak aktif."
```

Admin dapat mengubah status user melalui halaman detail user.

Proses perubahan status dilakukan melalui request `POST` dan dilindungi dengan CSRF token.

---

## 10. Password

Password pengguna tidak disimpan dalam bentuk plaintext.

Saat user dibuat, password diproses menggunakan fungsi hashing Django:

```python
make_password(password)
```

Hasil hashing disimpan pada field:

```text
passwordHash
```

Saat login, sistem melakukan verifikasi menggunakan:

```python
check_password(password, password_hash)
```

Dengan demikian, sistem tidak perlu menyimpan password asli pengguna di database.

Fitur password yang tersedia meliputi:

* Password saat pembuatan user.
* Verifikasi password saat login.
* Perubahan password oleh pengguna.
* Reset password oleh Admin.

Pada perubahan password, sistem juga memeriksa password lama sebelum memperbarui password baru.

Password baru harus berbeda dari password lama.

Password tidak dicatat dalam audit log.

---

## 11. Profile

Pengguna yang telah login dapat melihat informasi profile melalui:

```text
/profile/
```

Informasi yang ditampilkan meliputi:

* Nama.
* Username.
* Email.
* Role.
* Status akun.

View profile menggunakan decorator:

```python
@login_required_custom
```

Sehingga pengguna yang belum login tidak dapat membuka halaman profile.

Jika data user berdasarkan `user_id` pada session tidak ditemukan, session akan dihapus dan pengguna diarahkan kembali ke halaman login.

Pengguna juga dapat mengakses halaman perubahan password melalui:

```text
/profile/password/
```

---

## 12. Audit Log

Audit log digunakan untuk mencatat aktivitas penting yang dilakukan pengguna dalam sistem.

Data audit log disimpan pada collection:

```text
audit_logs
```

Aktivitas yang dicatat antara lain:

```text
login
logout
create_user
update_user
update_user_status
reset_password
update_user_role
```

Data audit dapat berisi:

* `userId`
* `username`
* `role`
* `action`
* `description`
* `targetType`
* `targetId`
* `ipAddress`
* `createdAt`

Contoh data audit:

```text
username: admin
role: Admin
action: login
description: User berhasil login.
targetType: user
targetId: <id-user>
createdAt: <waktu>
```

Audit log digunakan untuk membantu pencatatan aktivitas pengguna dan dapat digunakan sebagai dasar pemeriksaan aktivitas sistem.

Password pengguna tidak disimpan pada audit log.

---

## 13. CSRF dan Keamanan

Sistem menggunakan perlindungan keamanan Django untuk request yang berasal dari form.

Form dengan method `POST` menggunakan CSRF token:

```html
<form method="post">
    {% csrf_token %}
    ...
</form>
```

CSRF middleware Django tetap digunakan pada konfigurasi middleware.

Sistem tidak menggunakan:

```python
@csrf_exempt
```

untuk proses login, logout, maupun manajemen user.

Informasi konfigurasi sensitif disimpan menggunakan environment variable melalui file `.env`.

Contohnya:

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
MONGODB_URI
MONGODB_DATABASE
```

File `.env` juga tidak dimasukkan ke repository Git.

Untuk lingkungan production, konfigurasi keamanan tambahan dapat digunakan seperti HTTPS, secure session cookie, secure CSRF cookie, dan HTTP security headers.

---

## 14. URL Authentication

URL yang digunakan pada modul Authentication dan User Management adalah sebagai berikut:

| URL                           | Fungsi                               |
| ----------------------------- | ------------------------------------ |
| `/login/`                     | Halaman login                        |
| `/logout/`                    | Logout pengguna                      |
| `/profile/`                   | Melihat profile                      |
| `/profile/password/`          | Mengubah password                    |
| `/users/`                     | Melihat daftar user                  |
| `/users/create/`              | Membuat user                         |
| `/users/<id>/`                | Melihat detail user                  |
| `/users/<id>/edit/`           | Mengubah data user                   |
| `/users/<id>/status/`         | Mengaktifkan atau menonaktifkan user |
| `/users/<id>/reset-password/` | Reset password                       |
| `/users/<id>/role/`           | Mengubah role user                   |
| `/dashboard/`                 | Dashboard berdasarkan role           |

Halaman yang membutuhkan login menggunakan decorator authentication.

Halaman yang membutuhkan permission menggunakan decorator authorization.

---

## 15. Pengujian Authentication

Pengujian authentication dilakukan untuk memastikan proses autentikasi berjalan sesuai dengan kebutuhan sistem.

Pengujian meliputi:

### 15.1 Password Hashing

Memastikan password yang disimpan pada database tidak sama dengan password asli.

### 15.2 Login Berhasil

Memastikan pengguna dapat login menggunakan username dan password yang benar.

### 15.3 Password Salah

Memastikan login ditolak ketika password yang diberikan salah.

### 15.4 Username Tidak Ditemukan

Memastikan login ditolak ketika username tidak terdapat pada database.

### 15.5 User Inactive

Memastikan user dengan status `inactive` tidak dapat login.

### 15.6 Change Password

Memastikan pengguna dapat mengganti password setelah memasukkan password lama yang benar.

### 15.7 Login View

Memastikan proses login melalui halaman `/login/` dapat membuat session.

### 15.8 Logout

Memastikan logout menghapus session pengguna dan mengarahkan pengguna kembali ke halaman login.

### 15.9 Inactive User Login View

Memastikan user yang sudah dinonaktifkan tetap tidak dapat login melalui halaman `/login/`.

Pengujian dapat dijalankan menggunakan:

```bash
python manage.py test apps.authentication
```

---

## 16. Pengujian Authorization

Pengujian authorization dilakukan untuk memastikan setiap role hanya dapat mengakses fitur yang sesuai dengan permission-nya.

Contoh pengujian yang dilakukan adalah:

| Role     | User Management | Sales | Procurement |
| -------- | --------------: | ----: | ----------: |
| Admin    |             200 |   200 |         200 |
| Kasir    |             403 |   200 |         403 |
| Pengurus |             403 |   403 |         200 |
| Anggota  |             403 |   403 |         403 |

Keterangan:

```text
200 = akses diizinkan
403 = akses ditolak
```

Selain itu, pengguna yang belum login diuji untuk memastikan request ke halaman yang dilindungi menghasilkan redirect ke:

```text
/login/
```

Pengujian ini menunjukkan bahwa authorization dilakukan pada sisi server melalui permission decorator.

Contoh:

```python
@permission_required_custom("sales")
def sales_test_view(request):
    ...
```

Jika role pengguna tidak memiliki permission `sales`, request tidak diteruskan ke view dan server memberikan response `403 Forbidden`.

---

## 17. Alur Authentication

Alur proses login sistem adalah:

```text
User
 |
 v
Halaman Login
 |
 v
Input Username dan Password
 |
 v
Cari User pada MongoDB
 |
 v
User ditemukan?
 |
 +---- Tidak ----> Pesan "Username atau password salah"
 |
 v
Verifikasi Password
 |
 +---- Salah ----> Pesan "Username atau password salah"
 |
 v
Periksa Status User
 |
 +---- Inactive ----> Pesan "Akun tidak aktif"
 |
 v
Buat Django Session
 |
 v
Catat Audit Log Login
 |
 v
Dashboard
```

Sedangkan proses logout:

```text
User
 |
 v
Logout
 |
 v
Catat Audit Log Logout
 |
 v
request.session.flush()
 |
 v
Session Dihapus
 |
 v
Redirect /login/
```

Dengan alur tersebut, sistem memastikan hanya user yang berhasil melewati proses authentication yang dapat mengakses halaman yang dilindungi.

---

## 18. Alur Authorization

Alur authorization dilakukan setelah request diterima oleh server:

```text
User Request
 |
 v
Cek Session
 |
 +---- Tidak Login ----> Redirect /login/
 |
 v
Ambil Role User
 |
 v
Cek Permission
 |
 +---- Tidak Memiliki Permission ----> HTTP 403
 |
 v
Permission Ditemukan
 |
 v
View/Fitur Dijalankan
 |
 v
Response
```

Contoh ketika Kasir mencoba membuka fitur manajemen user:

```text
Kasir
 |
 v
Request /users/
 |
 v
Session Valid
 |
 v
Role = Kasir
 |
 v
Cek permission "user_management"
 |
 v
Permission tidak ditemukan
 |
 v
HTTP 403 Forbidden
```

Sedangkan ketika Admin membuka fitur yang sama:

```text
Admin
 |
 v
Request /users/
 |
 v
Session Valid
 |
 v
Role = Admin
 |
 v
Cek permission "user_management"
 |
 v
Permission ditemukan
 |
 v
View dijalankan
 |
 v
HTTP 200
```

Pendekatan ini memastikan pembatasan akses dilakukan di server dan tidak hanya berdasarkan menu yang ditampilkan pada halaman.

---

## 19. Kesimpulan

Modul Authentication & Authorization pada Sistem Informasi Toko Koperasi digunakan untuk mengatur keamanan akses pengguna terhadap sistem.

Fitur authentication mencakup login, logout, session management, pemeriksaan status user, password hashing, profile, perubahan password, dan reset password. Data pengguna disimpan pada collection `users` di MongoDB, sedangkan password disimpan dalam bentuk hash.

Fitur authorization menggunakan role dan permission untuk membatasi akses terhadap fitur sistem. Role yang digunakan terdiri dari Admin, Kasir, Pengurus, dan Anggota. Pemeriksaan permission dilakukan pada sisi server menggunakan decorator sehingga pengguna yang tidak memiliki permission akan mendapatkan response `403 Forbidden`.

Sistem juga menyediakan manajemen user, perubahan status user, perubahan role, dan audit log untuk mencatat aktivitas penting pengguna. Perlindungan CSRF diterapkan pada form POST dan konfigurasi sensitif disimpan melalui environment variable.

Berdasarkan pengujian authentication dan authorization, sistem telah memiliki dasar mekanisme keamanan yang diperlukan untuk digunakan oleh modul-modul lain pada Sistem Informasi Toko Koperasi.
