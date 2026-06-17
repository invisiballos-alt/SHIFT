from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Booking
from app.schemas import BookingCreate
from fastapi import HTTPException, status
from datetime import date

ALLOWED_SLOTS = ["09:00-11:00", "11:00-13:00", "13:00-15:00", "15:00-17:00", "17:00-19:00"]
ROOMS = ["Room-A", "Room-B", "Room-C"]

async def get_available_slots(db: AsyncSession, room_id: str, booking_date: date):
    if room_id not in ROOMS:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    
    stmt = select(Booking.slot).where(Booking.room_id == room_id, Booking.date == booking_date)
    result = await db.execute(stmt)
    booked_slots = result.scalars().all()
    
    return [slot for slot in ALLOWED_SLOTS if slot not in booked_slots]

async def create_booking(db: AsyncSession, booking_data: BookingCreate):
    if booking_data.room_id not in ROOMS:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    if booking_data.slot not in ALLOWED_SLOTS:
        raise HTTPException(status_code=400, detail="Неверный временной слот")
        
    stmt = select(Booking).where(
        Booking.room_id == booking_data.room_id,
        Booking.date == booking_data.date,
        Booking.slot == booking_data.slot
    )
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Этот слот уже забронирован")
        
    new_booking = Booking(**booking_data.model_dump())
    db.add(new_booking)
    await db.commit()
    await db.refresh(new_booking)
    return new_booking

async def cancel_booking(db: AsyncSession, booking_id: int, user_id: str, is_admin: bool):
    stmt = select(Booking).where(Booking.id == booking_id)
    result = await db.execute(stmt)
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
        
    if not is_admin and booking.employee_id != user_id:
        raise HTTPException(status_code=403, detail="Доступ запрещен к чужому бронированию")
        
    await db.delete(booking)
    await db.commit()
    return {"detail": "Бронирование успешно отменено"}
