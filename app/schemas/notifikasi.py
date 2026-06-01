from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class NotifikasiResponse(BaseModel):
    id: int
    user_id: int
    pesan: str
    tipe: Optional[str] = "status_update"
    pengajuan_id: Optional[int] = None
    metadata: Optional[dict[str, Any]] = Field(None, validation_alias="metadata_json")
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
