# ISSUE-001: WebP Batch & Single Image Compressor CLI Engine

## 1. Title
**Implement High-Performance CLI Image Converter & Compressor (PNG/JPEG/JPG/JPE to WebP)**

---

## 2. Overview
Issue ini menetapkan spesifikasi teknis dan panduan implementasi untuk membangun aplikasi Command Line Interface (CLI) berbasis Python yang efisien dan andal. Aplikasi ini bertugas membaca, mengompresi, dan mengonversi berkas gambar dengan format raster populer (`.png`, `.jpg`, `.jpeg`, `.jpe`) menjadi format WebP modern (`.webp`).

### Core Capabilities:
- **Default Workflow:** Pemindaian otomatis folder lokal `input/` dan penyimpanan hasil konversi terkompresi di folder `output/`.
- **Flexible Path Routing:** Mendukung kustomisasi direktori input dan output melalui flag CLI.
- **Conversion Scope & Capacity:** 
  * Mendukung pemrosesan batch tanpa batasan kuota file (*unlimited batch processing*) melalui arsitektur *stream generator* hemat memori $O(1)$.
  * Mendukung pemrosesan berkas tunggal (*single-file mode*).
  * Opsi pembatasan jumlah file (*batch limit*) untuk kebutuhan pengujian atau *chunking*.
- **Compression Control:** Pengaturan rasio kompresi (*quality factor*) dari 1 sampai 100 dengan opsi kompresi *lossless*.
- **Intelligent Alpha & Color-Space Handling:** Penanganan transparansi kanal Alpha (RGBA/LA/Palette) dan konversi profil warna (seperti CMYK) agar tidak menghasilkan artefak atau crash saat di-encode ke WebP.
- **Rich Terminal UX:** Indikator progres interaktif, estimasi waktu tersisa (ETA), tabel statistik ukuran sebelum vs. sesudah kompresi, serta logging visual bersih.

---

## 3. Tech Stack & Dependencies

### Runtime Environment:
- **Python:** 3.9+ (rekomendasi Python 3.10 atau 3.11 untuk efisiensi I/O).

### Primary Dependencies:
1. **Pillow (PIL Fork) `>= 10.2.0`**:
   - Engine inti pemrosesan gambar dan *encoding* WebP (via pustaka libwebp bawaan).
2. **rich `>= 13.7.0`**:
   - Penyedia komponen terminal UI: progress bar (`rich.progress`), tabel ringkasan hasil (`rich.table`), pesan error berformat (`rich.console`), dan status spinner.
3. **argparse (Standard Library)**:
   - Handler parsing argumen CLI bawaan Python tanpa overhead dependensi eksternal berlebih.
4. **pathlib (Standard Library)**:
   - Pengelolaan path sistem berkas lintas platform (Windows/macOS/Linux).

### File Blueprint:
Developer pelaksana wajib menyusun struktur repositori sebagai berikut:
```text
Kompresor to WEBP/
├── input/                  # Direktori input default (auto-generated)
├── output/                 # Direktori output default (auto-generated)
├── converter/              # Core logic package
│   ├── __init__.py
│   ├── engine.py           # Logika kompresi Pillow & transformasi warna
│   └── validator.py        # Validasi ekstensi, berkas corrupt, & nama berkas
├── main.py                 # CLI Entrypoint & Argument Parser
├── requirements.txt        # Definisi dependensi pustaka
├── README.md               # Dokumentasi pengguna (Manual Book)
└── issue.md                # Dokumen spesifikasi teknis ini
```

---

## 4. Step-by-Step Implementation Plan

Berikut urutan pengerjaan sekuensial yang harus dieksekusi oleh developer/model pelaksana. Berikan tanda centang `[x]` setelah setiap tahapan teruji dengan baik.

### Phase 1: Environment & Project Setup
- [ ] **Step 1.1**: Buat berkas `requirements.txt` yang memuat:
  ```text
  Pillow>=10.2.0
  rich>=13.7.0
  ```
- [ ] **Step 1.2**: Buat struktur modul Python (`converter/__init__.py`, `converter/engine.py`, `converter/validator.py`, `main.py`).

### Phase 2: Directory Bootstrapping & CLI Interface
- [ ] **Step 2.1**: Implementasikan fungsi bootstrapping direktori pada `main.py`:
  - Sistem harus memeriksa keberadaan folder `input/` dan `output/`.
  - Jika belum ada, buat direktori tersebut menggunakan `Path("input").mkdir(parents=True, exist_ok=True)` dan `Path("output").mkdir(parents=True, exist_ok=True)`.
- [ ] **Step 2.2**: Bangun antarmuka CLI pada `main.py` menggunakan `argparse.ArgumentParser` dengan argumen berikut:
  - `-i`, `--input`: Path direktori input kustom (default: `input/`).
  - `-o`, `--output`: Path direktori output kustom (default: `output/`).
  - `-f`, `--file`: Path berkas tunggal yang akan dikonversi (opsional, mematikan mode batch direktori jika didefinisikan).
  - `-q`, `--quality`: Faktor kualitas WebP (tipe: `int`, rentang: 1–100, default: `80`).
  - `-l`, `--lossless`: Flag boolean untuk mengaktifkan kompresi *lossless* WebP (default: `False`).
  - `-w`, `--overwrite`: Flag boolean untuk menimpa berkas jika berkas output dengan nama yang sama sudah ada di folder tujuan (default: `False`).
  - `-r`, `--recursive`: Flag boolean untuk memindai subfolder secara rekursif dalam mode direktori (default: `False`).
  - `-m`, `--method`: Tingkat usaha kompresi WebP (rentang 0-6, default: `6` untuk kompresi terbaik).
  - `-L`, `--limit`: Batasi jumlah maksimum berkas yang diproses dalam satu sesi batch (tipe: `int`, default: `None` / tanpa batas). Sangat berguna untuk pengujian cepat (*trial run*) pada folder berisi ribuan gambar.

### Phase 3: File Scanning, Streaming Generator & Case-Insensitive Validation
- [ ] **Step 3.1**: Daftarkan ekstensi yang didukung ke dalam format tuple lowercase:
  ```python
  SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.jpe')
  ```
- [ ] **Step 3.2**: Buat generator pemindai berkas hemat memori (*lazy generator*) pada `converter/validator.py`:
  - Gunakan `pathlib.Path.glob` (atau `rglob` jika `--recursive` aktif) yang menghasilkan *iterator/generator*, **bukan memuat semua file ke dalam list memory**.
  - Lakukan normalisasi ekstensi menggunakan `.suffix.lower()`.
  - Pastikan ekstensi `.jpe` (uppercase/lowercase/mixed case seperti `.JPE`, `.Jpe`) terdeteksi sama validnya dengan `.jpg` atau `.png`.
  - Jika argumen `--limit` aktif, potong aliran generator menggunakan `itertools.islice(generator, limit)` agar pemrosesan langsung berhenti setelah mencapai kuota tanpa membaca sisa ribuan file lainnya.
  - Filter hanya berkas asli (abaikan sub-direktori atau symlink yang tidak valid).

### Phase 4: Image Processing & Conversion Engine
- [ ] **Step 4.1**: Implementasikan fungsi pembacaan dan normalisasi gambar pada `converter/engine.py`:
  - Gunakan `ImageOps.exif_transpose(image)` agar orientasi foto dari metadata kamera EXIF tidak terputar.
  - Tangani variasi kanal warna (*Color Modes*):
    - **Mode `RGBA` & `LA`**: Pertahankan kanal alpha agar transparansi WebP sempurna.
    - **Mode `P` (Palette/Indexed) dengan transparansi**: Konversi secara eksplisit ke `RGBA` via `image.convert("RGBA")` untuk mencegah latar belakang transparan berubah menjadi hitam/artefak.
    - **Mode `CMYK`**: Konversi ke `RGB` via `image.convert("RGB")`. Pustaka WebP tidak mendukung CMYK dan akan melempar `OSError` jika tidak dikonversi terlebih dahulu.
    - **Mode `1` (1-bit pixels)** atau **Mode `L` (Grayscale)**: Konversi atau simpan sesuai kompatibilitas mode WebP.
- [ ] **Step 4.2**: Eksekusi penyimpanan ke WebP:
  - Bangun nama target output: mengganti ekstensi lama dengan `.webp`.
  - Panggil `image.save()` dengan parameter:
    ```python
    image.save(
        destination_path,
        format="WEBP",
        quality=quality,
        lossless=lossless,
        method=method
    )
    ```
  - Pastikan instance `Image` ditutup dengan benar (gunakan `with Image.open(...) as img:`) untuk menghindari *file descriptor leak*.

### Phase 5: Overwrite Protection & Collision Strategy
- [ ] **Step 5.1**: Periksa apakah berkas target `destination_path.exists()`:
  - Jika `True` dan flag `--overwrite` **tidak aktif**: Lewati (*skip*) konversi dan cetak pesan peringatan atau berikan nomor indeks pembeda (misal: `nama_file_1.webp`).
  - Jika `True` dan flag `--overwrite` **aktif**: Timpa berkas output.
  - Laporkan status berkas (`CONVERTED`, `SKIPPED`, `OVERWRITTEN`, `FAILED`) ke pencatat statistik.

### Phase 6: Error Handling & Fault Tolerance
- [ ] **Step 6.1**: Tangani berkas rusak (*corrupted files*):
  - Tangkap `PIL.UnidentifiedImageError` dan `IOError` secara terisolasi per berkas sehingga kegagalan satu berkas tidak menghentikan keseluruhan proses batch.
- [ ] **Step 6.2**: Tangani folder input kosong:
  - Jika tidak ada berkas yang cocok dengan `SUPPORTED_EXTENSIONS`, tampilkan pesan informatif berwarna kuning/oranye melalui `rich` dan keluar (*exit status code 0*) tanpa melempar Exception tak tertangani.
- [ ] **Step 6.3**: Tangani batasan hak akses (*permission error*):
  - Tangkap `PermissionError` saat membaca input atau menulis ke output, lalu berikan pesan instruksi yang jelas kepada pengguna.
- [ ] **Step 6.4**: Tangani proteksi gambar berukuran raksasa (*Pixel Bomb / Ultra High-Res*):
  - Tangkap `PIL.Image.DecompressionBombError` jika terdapat gambar beresolusi ekstrem (> 89 megapixel). Catat sebagai status `FAILED` dengan keterangan `Image too large (Pixel Bomb protection)` dan lanjutkan pemrosesan berkas berikutnya tanpa crash.

### Phase 7: Rich Terminal UI & Summary Reporting
- [ ] **Step 7.1**: Integrasikan `rich.progress.Progress` untuk visualisasi persentase, estimasi waktu, dan nama berkas yang sedang diproses.
- [ ] **Step 7.2**: Tampilkan tabel ringkasan akhir (`rich.table.Table`) yang memuat data:
  - Total berkas yang ditemukan.
  - Jumlah berkas berhasil, dilewati, dan gagal.
  - Akumulasi ukuran file sebelum vs sesudah (dalam KB/MB).
  - Persentase penghematan ruang penyimpanan (*Saved space %*).
  - Total durasi eksekusi.

---

## 5. User Documentation & Manual Book Requirements

Model/developer pelaksana wajib menyertakan atau memperbarui berkas `README.md` pada *root* repositori dengan isi panduan pengguna berikut:

````markdown
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
Melakukan kompresi tanpa kehilangan data piksel (sangat ideal untuk grafik vektor raster, screenshot teks, dan logo transparan):
```bash
python main.py --lossless
```

### 6. Menimpa Berkas yang Sudah Ada (`--overwrite` / `-w`)
Secara default, aplikasi akan melewati berkas yang sudah ada di folder output agar tidak terjadi kehilangan data. Gunakan flag `--overwrite` untuk memaksa penimpaan:
```bash
python main.py --overwrite
```

### 7. Memindai Sub-folder Secara Rekursif (`--recursive` / `-r`)
Memproses seluruh gambar di dalam folder utama beserta semua subdirektorinya:
```bash
python main.py -i "galeri/" -o "galeri_webp/" --recursive
```

---

## 📊 Daftar Lengkap Argumen CLI

| Argumen Singkat | Argumen Panjang | Tipe Data | Nilai Default | Keterangan |
| :--- | :--- | :--- | :--- | :--- |
| `-i` | `--input` | String | `input/` | Path folder sumber gambar |
| `-o` | `--output` | String | `output/` | Path folder tujuan hasil konversi |
| `-f` | `--file` | String | `None` | Path ke berkas spesifik (mode single-file) |
| `-q` | `--quality` | Integer | `80` | Kualitas kompresi WebP (1 - 100) |
| `-l` | `--lossless` | Flag | `False` | Aktifkan kompresi tanpa penurunan kualitas |
| `-w` | `--overwrite` | Flag | `False` | Timpa berkas jika nama target sudah ada |
| `-r` | `--recursive` | Flag | `False` | Pindai subfolder secara rekursif |
| `-m` | `--method` | Integer | `6` | Kompresi effort (0=tercepat, 6=terbaik) |
| `-L` | `--limit` | Integer | `None` | Batas maksimum berkas yang diproses (unlimited jika kosong) |
````

---

## 6. Edge Cases & Potential Pitfalls

Developer pelaksana wajib mengantisipasi dan memvalidasi skenario kritis berikut dalam kode:

1. **Ekstensi `.jpe` yang Kerap Terlewatkan:**
   - Format JPEG lawas atau keluaran kamera tertentu kerap memakai ekstensi `.jpe`.
   - Kode harus mengenali tuple `('.png', '.jpg', '.jpeg', '.jpe')` dengan normalisasi `.lower()` sebelum pengecekan.

2. **Pencegahan Data Loss (Duplicate & Collision Handling):**
   - Jika terdapat berkas `logo.png` dan `logo.jpg` pada folder input yang sama, keduanya akan berebut target `logo.webp` di folder output.
   - Solusi: Jika terjadi benturan nama dalam batch yang sama, berikan log peringatan dan tambahkan penanda unik (misal: `logo_png.webp` atau `logo_jpg.webp`) atau tanyakan perilaku via flag overwrite.

3. **Crash Warna CMYK ke WebP (`OSError: cannot write mode CMYK as WEBP`):**
   - Berkas JPEG cetak sering menggunakan mode CMYK. Encoder WebP libwebp tidak dapat memproses CMYK secara langsung.
   - Solusi: Deteksi `if img.mode == 'CMYK': img = img.convert('RGB')` sebelum proses kompresi.

4. **Transparansi Berbasis Palet (Mode `P` dengan info transparansi):**
   - Beberapa PNG teroptimasi menggunakan Mode `P` 8-bit dengan *color indexing*. Jika langsung disimpan ke WebP tanpa konversi, piksel transparan kerap berubah menjadi hitam pekat.
   - Solusi: Deteksi mode `P` dan ubah menjadi `RGBA` sebelum diserahkan ke encoder WebP.

5. **EXIF Orientation Meta-tag Loss:**
   - Foto dari smartphone sering kali memiliki orientasi fisik berbeda yang hanya disimpan dalam tag EXIF (Orientation Tag). Jika di-load polos oleh Pillow, gambar hasil konversi dapat terputar 90 atau 180 derajat.
   - Solusi: Gunakan `PIL.ImageOps.exif_transpose` segera setelah membuka gambar.

6. **Berkas Kosong (0-byte file) & File Corrupt:**
   - Adanya berkas kosong atau berkas yang terputus saat diunduh dapat memicu `PIL.UnidentifiedImageError`.
   - Solusi: Blok `try...except (UnidentifiedImageError, OSError)` lokal per berkas harus mencatat error dan melanjutkan pemrosesan sisa berkas lainnya.

7. **Kerapuhan Pemakaian Memori pada Batch Besar (Memory Leak):**
   - Memproses ribuan berkas tanpa menutup pointer gambar dapat menghabiskan RAM.
   - Solusi: Gunakan *context manager* `with Image.open(path) as img:` untuk memastikan pembebasan memori sesegera mungkin setelah kompresi selesai.

8. **Kapasitas Skalabilitas Batch (Berapa Banyak File yang Dapat Ditangani):**
   - **Batas Alami:** **Tidak ada batasan buatan (*no arbitrary file count limit*)**. Sistem sanggup memproses 10 hingga 50.000+ berkas dalam satu folder.
   - **Arsitektur Memori:** Menggunakan pola *Generator Streaming* ($O(1)$ memory complexity). Penggunaan RAM hanya dipengaruhi oleh resolusi 1 gambar yang sedang aktif dibuka, bukan total jumlah gambar dalam folder.
   - **Mitigasi Durasi:** Untuk direktori dengan puluhan ribu file, pengguna dapat menggunakan flag `--limit` untuk pemrosesan bertahap (*chunking*).

9. **Proteksi Pixel Bomb / Decompression Bomb (Resolusi Ekstrem):**
   - Berkas dengan resolusi raksasa (> 89 megapixel) memicu `PIL.Image.DecompressionBombError` demi keamanan memori.
   - Solusi: Tangkap error ini secara spesifik pada `converter/engine.py`, catat file tersebut ke dalam daftar `FAILED`, dan lanjutkan pemrosesan file berikutnya tanpa crash.

---

## 7. Acceptance Criteria (Definition of Done)

Fitur dinyatakan **SELESAI (100% COMPLETE)** jika memenuhi seluruh checklist verifikasi berikut:

- [ ] **AC-1 (Auto Directory Bootstrap):** Saat aplikasi dijalankan pertama kali tanpa argumen di direktori kosong, folder `input/` dan `output/` otomatis tercipta tanpa error.
- [ ] **AC-2 (Format Support):** Sistem berhasil mengonversi berkas `.png`, `.jpg`, `.jpeg`, dan `.jpe` (baik huruf kecil maupun kapital: `.PNG`, `.JPG`, `.JPE`) menjadi berkas berekstensi `.webp`.
- [ ] **AC-3 (Alpha Channel Integrity):** PNG dengan latar belakang transparan tetap transparan di berkas `.webp` keluaran (tidak terdapat bingkai hitam atau distorsi warna latar).
- [ ] **AC-4 (Quality Control):** Nilai flag `--quality` berpengaruh nyata terhadap ukuran berkas keluaran (misal: pengujian kualitas 30 menghasilkan ukuran berkas lebih kecil dibanding kualitas 90).
- [ ] **AC-5 (Single File Mode):** Perintah `python main.py -f <path_ke_file>` hanya mengonversi berkas tersebut ke direktori target tanpa menyentuh berkas lain di folder `input/`.
- [ ] **AC-6 (Custom Path):** Argumen `-i <custom_input>` dan `-o <custom_output>` bekerja sesuai path yang diberikan pengguna, termasuk path berspasi.
- [ ] **AC-7 (Crash-Resistant Execution):** Jika di dalam folder input terdapat berkas corrupt, berkas non-gambar dengan ekstensi palsu, atau file berukuran 0-byte, proses batch tidak terhenti dan berkas valid lainnya tetap sukses dikonversi.
- [ ] **AC-8 (Terminal Summary & UX):** Menampilkan progress bar yang halus dan tabel ringkasan di akhir proses yang menunjukkan jumlah berkas, total penghematan ukuran (*bytes saved* / rasio kompresi), dan waktu pengerjaan.
- [ ] **AC-9 (Documentation):** Berkas `README.md` terpasang di root direktori dengan panduan lengkap dan contoh perintah siap pakai.
- [ ] **AC-10 (Batch Scalability & Limit Control):** Pemrosesan batch skala besar (> 1.000 file) berjalan dengan konsumsi memori stabil ($O(1)$ RAM), serta flag `--limit <N>` / `-L <N>` secara presisi membatasi konversi hanya pada N berkas pertama.

