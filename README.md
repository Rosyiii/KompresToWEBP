# WebP Image Compressor CLI 🚀

Aplikasi Command Line Interface (CLI) berbasis Python berkinerja tinggi untuk mengompresi dan mengonversi berkas gambar (`.png`, `.jpg`, `.jpeg`, `.jpe`) menjadi format `.webp` modern dengan kompresi optimal dan dukungan transparansi penuh.

---

## 📁 Panduan Alur Kerja Direktori (Input & Output)

Sistem ini didesain dengan konsep zero-configuration secara default:
1. **Folder Sumber (Input):** Taruh semua gambar yang ingin Anda proses ke dalam folder:
   ```text
   input/
   ```
   *(Sistem akan otomatis membuat folder ini jika belum tersedia).*
2. **Folder Hasil (Output):** Seluruh gambar WebP hasil konversi akan otomatis tersedia di folder:
   ```text
   output/
   ```
   *(Nama file tetap sama, hanya ekstensi yang diubah menjadi `.webp`).*

---

## ⚙️ Persyaratan Sistem & Instalasi

1. Pastikan Anda telah menginstal **Python 3.9+**.
2. Buka terminal pada folder proyek ini, lalu buat dan aktifkan virtual environment (opsional tetapi direkomendasikan):
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```
3. Pasang dependensi yang diperlukan:
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Panduan Penggunaan & Contoh Perintah CLI

### 0. Melihat Panduan & Bantuan CLI (`--help` / `-h`)
Melihat daftar seluruh perintah, opsi, dan nilai default langsung dari terminal:
```bash
python main.py --help
# atau versi singkat:
python main.py -h
```

### 1. Konversi Default (Batch Mode)
Memproses seluruh gambar di dalam folder `input/` ke folder `output/` dengan kualitas standar (80):
```bash
python main.py
```

### 2. Menyesuaikan Kualitas Kompresi (`--quality` / `-q`)
Atur rasio kualitas gambar dari 1 (terkecil, kualitas rendah) hingga 100 (kualitas tertinggi):
```bash
# Kompresi tinggi (ukuran sangat kecil)
python main.py --quality 65

# Kualitas tinggi (sedikit kompresi)
python main.py -q 92
```

### 3. Menggunakan Direktori Input & Output Kustom (`-i` & `-o`)
Tentukan direktori sumber dan tujuan kustom di luar folder bawaan:
```bash
python main.py -i "D:/Photos/Vacation" -o "D:/Photos/WebP_Export"
```

### 4. Konversi Berkas Tunggal (`--file` / `-f`)
Mengonversi satu berkas spesifik tanpa memproses seluruh isi folder:
```bash
python main.py --file "input/banner-hero.png"
```
Atau simpan hasil konversi berkas tunggal ke folder kustom:
```bash
python main.py -f "gambar_produk.jpg" -o "assets/webp/" -q 85
```

### 5. Mengaktifkan Mode Lossless (`--lossless` / `-l`)
Melakukan kompresi tanpa membuang satu pun data piksel (kualitas 100% identik dengan aslinya). Sangat ideal untuk:
- Logo dan ikon transparan
- Screenshot UI dengan teks kecil/tajam
- Ilustrasi garis/vektor yang rentan buram jika menggunakan lossy JPEG/WebP
```bash
python main.py --lossless
```

### 6. Perilaku Penimpaan Berkas (`-w` / `--no-overwrite`)
Secara default, aplikasi **selalu menimpa (`overwrite=True`)** berkas di folder output jika terdapat file dengan nama yang sama. Jika Anda ingin **melewati / tidak menimpa** berkas yang sudah ada, gunakan flag:
```bash
python main.py --no-overwrite
```

### 7. Memindai Sub-folder Secara Rekursif (`--recursive` / `-r`)
Memproses seluruh gambar di dalam folder utama beserta semua subdirektorinya:
```bash
python main.py -i "galeri/" -o "galeri_webp/" --recursive
```

### 8. Membatasi Jumlah Berkas Terurut (`--limit` / `-L`)
Seluruh gambar yang ditemukan akan **diurutkan dari A ke Z (Ascending)** terlebih dahulu, kemudian dieksekusi sebanyak kuota yang Anda tentukan:
```bash
# Mengonversi 10 gambar pertama secara urut alfabet
python main.py --limit 10
```

### 9. Mengatur Usaha Kompresi (`--method` / `-m`)
Mengatur seberapa keras algoritma WebP menganalisis gambar untuk mengecilkan ukuran berkas (rentang 0-6, default: 6):
- `0`: Paling cepat (*fast encoding*), ukuran berkas sedikit lebih besar.
- `6`: Paling optimal (*best compression*), ukuran berkas paling kecil tanpa mengurangi kualitas visual.
```bash
# Kompresi ultra-cepat
python main.py -m 0
```

---

## 📊 Daftar Lengkap Argumen CLI

| Argumen Singkat | Argumen Panjang | Tipe Data | Nilai Default | Keterangan |
| :--- | :--- | :--- | :--- | :--- |
| `-h` | `--help` | Flag | - | Tampilkan panduan bantuan dan daftar seluruh argumen |
| `-i` | `--input` | String | `input/` | Path folder sumber gambar |
| `-o` | `--output` | String | `output/` | Path folder tujuan hasil konversi |
| `-f` | `--file` | String | `None` | Path ke berkas spesifik (mode single-file) |
| `-q` | `--quality` | Integer | `80` | Kualitas kompresi WebP (1 - 100) |
| `-l` | `--lossless` | Flag | `False` | Aktifkan kompresi tanpa penurunan kualitas (lossless) |
| `-w` | `--overwrite` / `--no-overwrite` | Boolean Flag | `True` (Aktif) | Timpa berkas jika nama target sudah ada (gunakan `--no-overwrite` untuk melewati) |
| `-r` | `--recursive` | Flag | `False` | Pindai subfolder secara rekursif |
| `-m` | `--method` | Integer | `6` | Usaha kompresi (0=tercepat, 6=paling optimal/kecil) |
| `-L` | `--limit` | Integer | `None` | Batasi jumlah berkas yang dieksekusi (diurutkan ASC) |

