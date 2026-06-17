from fastapi import FastAPI, Depends, Query, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import List
from app.database import get_db, engine, Base
from app.schemas import BookingCreate, BookingResponse, RoomStatus
import app.services as services

app = FastAPI(title="Сервис бронирования переговорных комнат")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/rooms/availability", response_model=List[RoomStatus])
async def get_rooms_availability(booking_date: date = Query(...), db: AsyncSession = Depends(get_db)):
    result = []
    for room_id in services.ROOMS:
        slots = await services.get_available_slots(db, room_id, booking_date)
        result.append(RoomStatus(room_id=room_id, available_slots=slots))
    return result

@app.post("/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def make_booking(booking_data: BookingCreate, x_user_id: str = Header(...), db: AsyncSession = Depends(get_db)):
    if booking_data.employee_id != x_user_id:
        raise HTTPException(status_code=403, detail="Нельзя создавать бронь за другого сотрудника")
    return await services.create_booking(db, booking_data)

@app.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: int, x_user_id: str = Header(...), x_role: str = Header("employee"), db: AsyncSession = Depends(get_db)):
    is_admin = (x_role == "admin")
    return await services.cancel_booking(db, booking_id, user_id=x_user_id, is_admin=is_admin)
