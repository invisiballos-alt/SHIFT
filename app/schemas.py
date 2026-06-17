from pydantic import BaseModel, Field
from datetime import date
from typing import List

class BookingBase(BaseModel):
    room_id: str
    date: date
    slot: str

class BookingCreate(BookingBase):
    employee_id: str

class BookingResponse(BookingBase):
    id: int
    employee_id: str

    class Config:
        from_attributes = True

class RoomStatus(BaseModel):
    room_id: str
    available_slots: List[str]
