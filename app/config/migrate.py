from sqlalchemy import inspect, text
from app.config.database import engine


def run_migrations():
    """Sinkronkan skema database dengan model SQLAlchemy (tanpa hapus data)."""
    inspector = inspect(engine)

    if not inspector.has_table("pengajuan"):
        return

    columns = {col["name"] for col in inspector.get_columns("pengajuan")}

    with engine.begin() as conn:
        if "kategori" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE pengajuan "
                    "ADD COLUMN kategori VARCHAR(100) NULL AFTER jenis_pengajuan"
                )
            )
