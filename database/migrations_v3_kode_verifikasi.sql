-- E-Office v3 — Kode verifikasi surat (QR/Barcode)
USE db_eoffice;

ALTER TABLE pengajuan
  ADD COLUMN kode_verifikasi VARCHAR(32) NULL;

UPDATE pengajuan
SET kode_verifikasi = UPPER(
  CONCAT('EO-', YEAR(created_at), '-', LPAD(id, 4, '0'), '-',
         SUBSTRING(MD5(CONCAT(id, '-', created_at)), 1, 6))
)
WHERE kode_verifikasi IS NULL
  AND LOWER(status) IN ('selesai', 'disetujui');

CREATE UNIQUE INDEX uq_pengajuan_kode_verifikasi ON pengajuan (kode_verifikasi);
