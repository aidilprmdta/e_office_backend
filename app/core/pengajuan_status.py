from enum import Enum


class PengajuanStatus(str, Enum):
    DIAJUKAN = "diajukan"
    DIPROSES_ADMIN = "diproses_admin"
    MENUNGGU_TTD = "menunggu_tanda_tangan"
    PERLU_REVISI = "perlu_revisi"
    SELESAI = "selesai"
    DITOLAK = "ditolak"


ALLOWED_TRANSITIONS = {
    PengajuanStatus.DIAJUKAN: {
        PengajuanStatus.DIPROSES_ADMIN,
        PengajuanStatus.PERLU_REVISI,
        PengajuanStatus.DITOLAK,
    },
    PengajuanStatus.DIPROSES_ADMIN: {
        PengajuanStatus.MENUNGGU_TTD,
        PengajuanStatus.PERLU_REVISI,
        PengajuanStatus.SELESAI,
        PengajuanStatus.DITOLAK,
    },
    PengajuanStatus.MENUNGGU_TTD: {
        PengajuanStatus.SELESAI,
        PengajuanStatus.PERLU_REVISI,
        PengajuanStatus.DITOLAK,
    },
    PengajuanStatus.PERLU_REVISI: {PengajuanStatus.DIAJUKAN},
    PengajuanStatus.SELESAI: set(),
    PengajuanStatus.DITOLAK: set(),
}

TRACKING_STEPS = [
    PengajuanStatus.DIAJUKAN,
    PengajuanStatus.DIPROSES_ADMIN,
    PengajuanStatus.MENUNGGU_TTD,
    PengajuanStatus.SELESAI,
]

LEGACY_STATUS_MAP = {
    "pending": PengajuanStatus.DIAJUKAN.value,
    "disetujui": PengajuanStatus.SELESAI.value,
    "ditolak": PengajuanStatus.DITOLAK.value,
}


def normalize_status(status: str | None) -> str:
    if not status:
        return PengajuanStatus.DIAJUKAN.value
    s = status.strip().lower()
    return LEGACY_STATUS_MAP.get(s, s)


def assert_transition(old_status: str, new_status: str) -> None:
    old = normalize_status(old_status)
    new = normalize_status(new_status)
    try:
        old_e = PengajuanStatus(old)
        new_e = PengajuanStatus(new)
    except ValueError as exc:
        raise ValueError(f"Status tidak valid: {old} atau {new}") from exc
    allowed = ALLOWED_TRANSITIONS.get(old_e, set())
    if new_e not in allowed:
        raise ValueError(f"Transisi {old} → {new} tidak diizinkan")
