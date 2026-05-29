from pydantic import BaseModel
from datetime import datetime


class NotifikasiResponse(BaseModel):
    id: int
    user_id: int
    pesan: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
