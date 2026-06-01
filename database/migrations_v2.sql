-- ============================================================
-- E-Office Kampus — Migrasi Database v2.0
-- Jalankan di MySQL (phpMyAdmin / Workbench) pada database db_eoffice
-- Backup database terlebih dahulu!
-- ============================================================

USE db_eoffice;

-- ------------------------------------------------------------
-- 1. Tabel USERS — kolom kontak (WhatsApp / Email notifikasi)
-- ------------------------------------------------------------
-- Jika kolom sudah ada, abaikan error "Duplicate column"
ALTER TABLE users ADD COLUMN email VARCHAR(120) NULL;
ALTER TABLE users ADD COLUMN no_hp VARCHAR(20) NULL;

-- ------------------------------------------------------------
-- 2. Tabel PENGAJUAN — workflow & dokumen hasil
-- ------------------------------------------------------------
ALTER TABLE pengajuan
  ADD COLUMN catatan_revisi TEXT NULL;

ALTER TABLE pengajuan
  ADD COLUMN file_hasil_url VARCHAR(255) NULL;

ALTER TABLE pengajuan
  ADD COLUMN updated_at DATETIME NULL;

ALTER TABLE pengajuan
  MODIFY COLUMN status VARCHAR(50) DEFAULT 'diajukan';

-- Migrasi nilai status lama
UPDATE pengajuan SET status = 'diajukan'
  WHERE LOWER(status) IN ('pending', '') OR status IS NULL;

UPDATE pengajuan SET status = 'selesai'
  WHERE LOWER(status) = 'disetujui';

UPDATE pengajuan SET status = 'ditolak'
  WHERE LOWER(status) = 'ditolak';

-- ------------------------------------------------------------
-- 3. Tabel NOTIFIKASI — metadata & link pengajuan
-- ------------------------------------------------------------
ALTER TABLE notifikasi
  ADD COLUMN tipe VARCHAR(30) DEFAULT 'status_update';

ALTER TABLE notifikasi
  ADD COLUMN pengajuan_id INT NULL;

ALTER TABLE notifikasi
  ADD COLUMN metadata JSON NULL;

ALTER TABLE notifikasi
  ADD CONSTRAINT fk_notif_pengajuan
  FOREIGN KEY (pengajuan_id) REFERENCES pengajuan(id) ON DELETE SET NULL;

-- ------------------------------------------------------------
-- 4. Tabel baru — LOG TIMELINE STATUS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pengajuan_status_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  pengajuan_id INT NOT NULL,
  status_lama VARCHAR(50) NULL,
  status_baru VARCHAR(50) NOT NULL,
  catatan TEXT NULL,
  diubah_oleh INT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_pengajuan_id (pengajuan_id),
  CONSTRAINT fk_log_pengajuan
    FOREIGN KEY (pengajuan_id) REFERENCES pengajuan(id) ON DELETE CASCADE,
  CONSTRAINT fk_log_user
    FOREIGN KEY (diubah_oleh) REFERENCES users(id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- 5. (Opsional) Isi log awal dari pengajuan yang sudah ada
-- ------------------------------------------------------------
INSERT INTO pengajuan_status_log (pengajuan_id, status_lama, status_baru, catatan)
SELECT id, NULL, status, 'Migrasi data — status awal'
FROM pengajuan
WHERE id NOT IN (SELECT DISTINCT pengajuan_id FROM pengajuan_status_log);

-- ============================================================
-- Status workflow yang valid:
--   diajukan | diproses_admin | menunggu_tanda_tangan
--   perlu_revisi | selesai | ditolak
-- ============================================================
