from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Date, UniqueConstraint
from app.database import Base
from datetime import date

class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    room_id: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    slot: Mapped[str] = mapped_column(String(20), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint('room_id', 'date', 'slot', name='_room_date_slot_uc'),
    )
