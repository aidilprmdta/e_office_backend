from sqlalchemy import inspect, text
from app.config.database import engine


def _add_column_if_missing(conn, table: str, column: str, ddl: str, columns: set):
    if column not in columns:
        conn.execute(text(f"ALTER TABLE {table} {ddl}"))


def run_migrations():
    """Sinkronkan skema database dengan model SQLAlchemy (tanpa hapus data)."""
    inspector = inspect(engine)

    if inspector.has_table("pengajuan"):
        columns = {col["name"] for col in inspector.get_columns("pengajuan")}
        with engine.begin() as conn:
            _add_column_if_missing(
                conn,
                "pengajuan",
                "kategori",
                "ADD COLUMN kategori VARCHAR(100) NULL",
                columns,
            )
            columns = {col["name"] for col in inspector.get_columns("pengajuan")}
            _add_column_if_missing(
                conn,
                "pengajuan",
                "catatan_revisi",
                "ADD COLUMN catatan_revisi TEXT NULL",
                columns,
            )
            columns = {col["name"] for col in inspector.get_columns("pengajuan")}
            _add_column_if_missing(
                conn,
                "pengajuan",
                "file_hasil_url",
                "ADD COLUMN file_hasil_url VARCHAR(255) NULL",
                columns,
            )
            columns = {col["name"] for col in inspector.get_columns("pengajuan")}
            _add_column_if_missing(
                conn,
                "pengajuan",
                "updated_at",
                "ADD COLUMN updated_at DATETIME NULL",
                columns,
            )
            conn.execute(
                text(
                    "UPDATE pengajuan SET status = 'diajukan' "
                    "WHERE LOWER(status) IN ('pending', '') OR status IS NULL"
                )
            )
            conn.execute(
                text(
                    "UPDATE pengajuan SET status = 'selesai' "
                    "WHERE LOWER(status) = 'disetujui'"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE pengajuan MODIFY COLUMN status VARCHAR(50) "
                    "DEFAULT 'diajukan'"
                )
            )

    if inspector.has_table("notifikasi"):
        columns = {col["name"] for col in inspector.get_columns("notifikasi")}
        with engine.begin() as conn:
            _add_column_if_missing(
                conn,
                "notifikasi",
                "tipe",
                "ADD COLUMN tipe VARCHAR(30) DEFAULT 'status_update'",
                columns,
            )
            columns = {col["name"] for col in inspector.get_columns("notifikasi")}
            _add_column_if_missing(
                conn,
                "notifikasi",
                "pengajuan_id",
                "ADD COLUMN pengajuan_id INT NULL",
                columns,
            )
            columns = {col["name"] for col in inspector.get_columns("notifikasi")}
            _add_column_if_missing(
                conn,
                "notifikasi",
                "metadata",
                "ADD COLUMN metadata JSON NULL",
                columns,
            )

    if inspector.has_table("users"):
        columns = {col["name"] for col in inspector.get_columns("users")}
        with engine.begin() as conn:
            _add_column_if_missing(
                conn,
                "users",
                "email",
                "ADD COLUMN email VARCHAR(120) NULL",
                columns,
            )
            columns = {col["name"] for col in inspector.get_columns("users")}
            _add_column_if_missing(
                conn,
                "users",
                "no_hp",
                "ADD COLUMN no_hp VARCHAR(20) NULL",
                columns,
            )

    inspector = inspect(engine)
    if not inspector.has_table("pengajuan_status_log"):
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE pengajuan_status_log (
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
                    )
                    """
                )
            )
